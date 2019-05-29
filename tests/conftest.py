import pytest
from requests.exceptions import HTTPError
from config_binding_service import get_consul_uri


class FakeResponse():
    def __init__(self, status_code, text):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise HTTPError(response=FakeResponse(404, ""))


@pytest.fixture
def expected_config():
    return {"deep": {"ALL YOUR SERVICE BELONG TO US": ['6.6.6.6:666', '7.7.7.7:777', '5.5.5.5:555', '5.5.5.5:555']},
            "doubledeep": {"sodeep": {"hello": "darkness"}}}


@pytest.fixture
def monkeyed_get_connection_info_from_consul():
    def _monkeyed_get_connection_info_from_consul(service_component_name):
        # shared monkeypatch. probably somewhat lazy because the function htis patches can be broken up.
        if service_component_name == "cdap":
            return '666.666.666.666:666'
        elif service_component_name == "testing_bravo.somedomain.com":
            return '7.7.7.7:777'
        elif service_component_name == "testing_alpha.somedomain.com":
            return '6.6.6.6:666'
        elif service_component_name == "testing_charlie.somedomain.com":
            return '5.5.5.5:555'
        elif service_component_name == "nonexistent_hope":
            return None  # the real function returns None here
        elif service_component_name == "cdap_serv.dcae.ecomp.somedomain.com":
            broker_ip = '1.1.1.1'
            broker_port = 444
            return "http://{0}:{1}/application/{2}".format(broker_ip, broker_port, service_component_name)
    return _monkeyed_get_connection_info_from_consul


@pytest.fixture
def monkeyed_requests_get():
    def _monkeyed_requests_get(url):
        if url == "{0}/v1/kv/test_service_component_name.unknown.unknown.unknown.dcae.onap.org:dti".format(get_consul_uri()):
            return FakeResponse(status_code=200, text='[{"LockIndex":0,"Key":"test_service_component_name.unknown.unknown.unknown.dcae.onap.org:dti","Flags":0,"Value":          "eyJteSIgOiAiZHRpIn0=","CreateIndex":4066524,"ModifyIndex":4066524}]')
        else:
            return FakeResponse(status_code=404, text="")
    return _monkeyed_requests_get


@pytest.fixture
def monkeyed_requests_put():
    def _monkeyed_requests_put(url, json):
        if url == "{0}/v1/txn".format(get_consul_uri()):
            key = json[0]["KV"]["Key"]
            if key == "test_service_component_name.unknown.unknown.unknown.dcae.onap.org":
                return FakeResponse(status_code=200, text='{"Results":[{"KV":{"LockIndex":0,"Key":"test_service_component_name.unknown.unknown.unknown.dcae.onap.org","Flags":0,"Value":"eyJteSIgOiAiYW1hemluZyBjb25maWcifQ==","CreateIndex":4051555,"ModifyIndex":4051555}},{"KV":{"LockIndex":0,"Key":"test_service_component_name.unknown.unknown.unknown.dcae.onap.org:dmaap","Flags":0,"Value":"eyJmb28iIDogImJhciJ9","CreateIndex":4051571,"ModifyIndex":4051571}},{"KV":{"LockIndex":0,"Key":"test_service_component_name.unknown.unknown.unknown.dcae.onap.org:dti","Flags":0,"Value":"eyJteSIgOiAiZHRpIn0=","CreateIndex":4066524,"ModifyIndex":4066524}},{"KV":{"LockIndex":0,"Key":"test_service_component_name.unknown.unknown.unknown.dcae.onap.org:policies/event","Flags":0,"Value":"eyJhY3Rpb24iOiAiZ2F0aGVyZWQiLCAidGltZXN0YW1wIjogIjIwMTgtMDItMTkgMTU6MzY6NDQuODc3MzgwIiwgInVwZGF0ZV9pZCI6ICJiYjczYzIwYS01ZmY4LTQ1MGYtODIyMy1kYTY3MjBhZGUyNjciLCAicG9saWNpZXNfY291bnQiOiAyfQ==","CreateIndex":4048564,"ModifyIndex":4048564}},{"KV":{"LockIndex":0,"Key":"test_service_component_name.unknown.unknown.unknown.dcae.onap.org:policies/items/DCAE_alex.Config_MS_alex_microservice","Flags":0,"Value":"eyJwb2xpY3lOYW1lIjogIkRDQUVfYWxleC5Db25maWdfTVNfYWxleF9taWNyb3NlcnZpY2UuMTMyLnhtbCIsICJwb2xpY3lDb25maWdNZXNzYWdlIjogIkNvbmZpZyBSZXRyaWV2ZWQhICIsICJyZXNwb25zZUF0dHJpYnV0ZXMiOiB7fSwgInBvbGljeUNvbmZpZ1N0YXR1cyI6ICJDT05GSUdfUkVUUklFVkVEIiwgIm1hdGNoaW5nQ29uZGl0aW9ucyI6IHsiT05BUE5hbWUiOiAiRENBRSIsICJOYW1lIjogIkRDQUUiLCAiQ29uZmlnTmFtZSI6ICJhbGV4X2NvbmZpZ19uYW1lIn0sICJjb25maWciOiB7InBvbGljeVNjb3BlIjogImFsZXhfcG9saWN5X3Njb3BlIiwgImNvbmZpZ05hbWUiOiAiYWxleF9jb25maWdfbmFtZSIsICJkZXNjcmlwdGlvbiI6ICJ0ZXN0IERDQUUgcG9saWN5LWhhbmRsZXIiLCAic2VydmljZSI6ICJhbGV4X3NlcnZpY2UiLCAicG9saWN5TmFtZSI6ICJhbGV4X3BvbGljeV9uYW1lIiwgInJpc2tMZXZlbCI6ICIzIiwgImtleTEiOiAidmFsdWUxIiwgInBvbGljeV9oZWxsbyI6ICJ3b3JsZCEiLCAiY29udGVudCI6IHsiZm9vIjogIm1pY3Jvc2VydmljZTMiLCAiZm9vX3VwZGF0ZWQiOiAiMjAxOC0wMS0zMFQxMzoyNTozMy4yMjJaIn0sICJyaXNrVHlwZSI6ICIxNzEyX0VURSIsICJndWFyZCI6ICJGYWxzZSIsICJ2ZXJzaW9uIjogIjAuMC4xIiwgImxvY2F0aW9uIjogIkNlbnRyYWwiLCAicG9saWN5X3VwZGF0ZWRfdHMiOiAiMjAxOC0wMi0xOVQxNTowOTo1NS4yMTdaIiwgInVwZGF0ZWRfcG9saWN5X2lkIjogIkRDQUVfYWxleC5Db25maWdfTVNfYWxleF9taWNyb3NlcnZpY2UiLCAicG9saWN5X3VwZGF0ZWRfdG9fdmVyIjogIjEzMiIsICJwcmlvcml0eSI6ICI0IiwgInBvbGljeV91cGRhdGVkX2Zyb21fdmVyIjogIjEzMSIsICJ0ZW1wbGF0ZVZlcnNpb24iOiAiMiIsICJ1dWlkIjogIjVlODdkN2M1LTBkYWYtNGI2Yi1hYjkyLTUzNjVjZjVkYjFlZiJ9LCAicHJvcGVydHkiOiBudWxsLCAidHlwZSI6ICJKU09OIiwgInBvbGljeVZlcnNpb24iOiAiMTMyIn0=","CreateIndex":4048564,"ModifyIndex":4065574}},{"KV":{"LockIndex":0,"Key":"test_service_component_name.unknown.unknown.unknown.dcae.onap.org:policies/items/DCAE_alex.Config_db_client_policy_id_value","Flags":0,"Value":"eyJwb2xpY3lOYW1lIjogIkRDQUVfYWxleC5Db25maWdfZGJfY2xpZW50X3BvbGljeV9pZF92YWx1ZS4xMzMueG1sIiwgInBvbGljeUNvbmZpZ01lc3NhZ2UiOiAiQ29uZmlnIFJldHJpZXZlZCEgIiwgInJlc3BvbnNlQXR0cmlidXRlcyI6IHt9LCAicG9saWN5Q29uZmlnU3RhdHVzIjogIkNPTkZJR19SRVRSSUVWRUQiLCAibWF0Y2hpbmdDb25kaXRpb25zIjogeyJPTkFQTmFtZSI6ICJEQ0FFIiwgIk5hbWUiOiAiRENBRSIsICJDb25maWdOYW1lIjogImFsZXhfY29uZmlnX25hbWUifSwgImNvbmZpZyI6IHsiZGJfY2xpZW50X3RzIjogIjIwMTctMTEtMjFUMTI6MTI6MTMuNjk2WiIsICJkYl9jbGllbnQiOiAiaXBzdW0iLCAicG9saWN5X2hlbGxvIjogIndvcmxkISIsICJwb2xpY3lfdXBkYXRlZF9mcm9tX3ZlciI6ICIxMzIiLCAidXBkYXRlZF9wb2xpY3lfaWQiOiAiRENBRV9hbGV4LkNvbmZpZ19kYl9jbGllbnRfcG9saWN5X2lkX3ZhbHVlIiwgInBvbGljeV91cGRhdGVkX3RzIjogIjIwMTgtMDItMTlUMTU6MDk6NTUuODEyWiIsICJwb2xpY3lfdXBkYXRlZF90b192ZXIiOiAiMTMzIn0sICJwcm9wZXJ0eSI6IG51bGwsICJ0eXBlIjogIkpTT04iLCAicG9saWN5VmVyc2lvbiI6ICIxMzMifQ==","CreateIndex":4048564,"ModifyIndex":4065570}},{"KV":{"LockIndex":0,"Key":"test_service_component_name.unknown.unknown.unknown.dcae.onap.org:rels","Flags":0,"Value":"WyJteS5hbWF6aW5nLnJlbGF0aW9uc2hpcCJd","CreateIndex":4051567,"ModifyIndex":4051567}}],"Errors":null,"Index":0,"LastContact":0,"KnownLeader":true}')
            elif key == "scn_exists":
                return FakeResponse(status_code=200, text='{"Results":[{"KV":{"LockIndex":0,"Key":"scn_exists","Flags":0,"Value":"eyJmb28zIiA6ICJiYXIzIn0=","CreateIndex":4067403,"ModifyIndex":4067403}},{"KV":{"LockIndex":0,"Key":"scn_exists:dmaap","Flags":0,"Value":"eyJmb280IiA6ICJiYXI0In0=","CreateIndex":4067410,"ModifyIndex":4067410}},{"KV":{"LockIndex":0,"Key":"scn_exists:rels","Flags":0,"Value":"WyJmb28iXQ==","CreateIndex":4067406,"ModifyIndex":4067406}},{"KV":{"LockIndex":0,"Key":"scn_exists_nord","Flags":0,"Value":"eyJmb281IiA6ICJiYXI1In0=","CreateIndex":4067340,"ModifyIndex":4067340}}],"Errors":null,"Index":0,"LastContact":0,"KnownLeader":true}')
            elif key == "scn_exists_nord":
                return FakeResponse(status_code=200, text='{"Results":[{"KV":{"LockIndex":0,"Key":"scn_exists_nord","Flags":0,"Value":"eyJmb281IiA6ICJiYXI1In0=","CreateIndex":4067340,"ModifyIndex":4067340}}],"Errors":null,"Index":0,"LastContact":0,"KnownLeader":true}')
            elif key == "test_resolve_scn":
                return FakeResponse(status_code=200, text='{"Results":[{"KV":{"LockIndex":0,"Key":"test_resolve_scn","Flags":0,"Value":"ewogICAgICAgICAgICAgICAgImRlZXAiIDogewogICAgICAgICAgICAgICAgICAgICJBTEwgWU9VUiBTRVJWSUNFIEJFTE9ORyBUTyBVUyIgOiAie3thbHBoYSxicmF2byxjaGFybGllfX0ifSwKICAgICAgICAgICAgICAgICJkb3VibGVkZWVwIiA6ICB7CiAgICAgICAgICAgICAgICAgICAgInNvZGVlcCIgOiB7ImhlbGxvIiA6ICI8PFdITz8+PiJ9fQogICAgICAgICAgICAgfQo=","CreateIndex":4068002,"ModifyIndex":4068002}},{"KV":{"LockIndex":0,"Key":"test_resolve_scn:dmaap","Flags":0,"Value":"eyJXSE8/IiA6ICJkYXJrbmVzcyJ9","CreateIndex":4068013,"ModifyIndex":4068013}},{"KV":{"LockIndex":0,"Key":"test_resolve_scn:rels","Flags":0,"Value":"WyJ0ZXN0aW5nX2FscGhhLnNvbWVkb21haW4uY29tIiwgInRlc3RpbmdfYnJhdm8uc29tZWRvbWFpbi5jb20iLCAidGVzdGluZ19jaGFybGllLnNvbWVkb21haW4uY29tIiwgInRlc3RpbmdfY2hhcmxpZS5zb21lZG9tYWluLmNvbSJd","CreateIndex":4068010,"ModifyIndex":4068010}}],"Errors":null,"Index":0,"LastContact":0,"KnownLeader":true}')
            elif key == "cbs_test_messed_up":
                return FakeResponse(status_code=200, text='{"Results":[{"KV":{"LockIndex":0,"Key":"cbs_test_messed_up","Flags":0,"Value":"eyJmb28iIDogImJhciJ9","CreateIndex":4864032,"ModifyIndex":4864052}},{"KV":{"LockIndex":0,"Key":"cbs_test_messed_up:badkey","Flags":0,"Value":"eyJub3QgYSBqc29ubm5uIFJFS1RUVFQ=","CreateIndex":4864075,"ModifyIndex":4864075}}],"Errors":null,"Index":0,"LastContact":0,"KnownLeader":true}')
            elif key == "scn_NOTexists":
                return FakeResponse(status_code=404, text="")
    return _monkeyed_requests_put
