import pytest
from ratvision.analytics.schema import sanitize_properties


def test_analytics_schema_allows_only_coarse_product_fields():
    props=sanitize_properties('app_started', {'app_version':'1.2.0','edition':'portable','monitor_count':2,'gpu_vendor':['NVIDIA'],'locale':'ru_RU','process_name':'EscapeFromTarkov.exe','path':'C:/x'})
    assert props == {'app_version':'1.2.0','edition':'portable','monitor_count':2}
    assert 'process_name' not in props and 'path' not in props and 'locale' not in props
