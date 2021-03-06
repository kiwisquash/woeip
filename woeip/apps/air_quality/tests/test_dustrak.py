from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from woeip.apps.air_quality import dustrak, models
from woeip.apps.air_quality.tests import factories

test_data_directory = Path(__file__).parent / 'data'


def get_target_data():
    """Load the target output"""
    target_output = pd.read_csv(test_data_directory / 'joined.csv', parse_dates=['time'])
    target_output.set_index('time', inplace=True)
    target_output = target_output.tz_localize('UTC')
    target_output.reset_index(inplace=True)

    return target_output


target_data = get_target_data()


def test_joiner():
    """Test the output of the function that joins GPS and air quality measurements based on time stamps"""
    with open(test_data_directory / 'dustrak.csv', 'rb') as f:
        contents = f.read().decode('utf-8')
    _, air_quality = dustrak.load_dustrak(contents, tz='America/Los_Angeles')

    with open(test_data_directory / 'gps.log', 'rb') as f:
        contents = f.read().decode('utf-8')
    gps = dustrak.load_gps(contents)

    with pytest.warns(UserWarning):
        joined_data = dustrak.join(air_quality, gps)

    for column in target_data:
        if column == 'time':
            assert all(target_data[column] == joined_data[column])
        else:
            assert np.allclose(target_data[column], joined_data[column])


@pytest.mark.django_db
def test_save():
    """Test ability to save a session of joined GPS/air quality data to the database, based on measurement/value"""
    session = factories.SessionFactory()
    dustrak.save(target_data, session)
    assert np.allclose(target_data['measurement'], models.Data.objects.values_list('value', flat=True))
