# -*- coding: utf-8 -*-

from http.client import OK

from tests import base
from openfisca_web_api_preview.app import create_app


client = create_app(base.tax_benefit_system).test_client()


# /variables

def test_return_code():
    variables_response = client.get('/variables')
    assert_equal(variables_response.status_code, OK)
