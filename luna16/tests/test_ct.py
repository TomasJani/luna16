from luna16.datasets import utils


def test_loading_ct_from_series_uid():
    series_uid = "1.3.6.1.4.1.14519.5.2.1.6279.6001.108197895896446896160048741492"
    ct_scan = utils.Ct.read_and_create_from_image(series_uid=series_uid)
    assert ct_scan.series_uid == series_uid
