"""Unit tests for portfolio.ratelimit — mocks rag.db."""
from unittest.mock import patch

from portfolio.ratelimit import (
    DAILY_CAP_DEFAULT,
    IP_DAILY_LIMIT,
    check_and_increment_ip,
    check_and_increment_rpd,
    get_today_status,
    hash_ip,
)


def test_hash_ip_is_deterministic():
    a = hash_ip("1.2.3.4")
    b = hash_ip("1.2.3.4")
    assert a == b
    assert a != hash_ip("5.6.7.8")
    assert len(a) == 64  # sha256 hex


@patch("portfolio.ratelimit.db.select")
@patch("portfolio.ratelimit.db.upsert")
def test_check_and_increment_ip_under_limit(mock_upsert, mock_select):
    mock_select.return_value = [{"count": 2}]
    status = check_and_increment_ip("hashval")
    assert status.allowed is True
    assert status.remaining == IP_DAILY_LIMIT - 3  # was 2, now 3
    mock_upsert.assert_called_once()


@patch("portfolio.ratelimit.db.select")
@patch("portfolio.ratelimit.db.upsert")
def test_check_and_increment_ip_at_limit(mock_upsert, mock_select):
    mock_select.return_value = [{"count": IP_DAILY_LIMIT}]
    status = check_and_increment_ip("hashval")
    assert status.allowed is False
    assert status.remaining == 0
    mock_upsert.assert_not_called()


@patch("portfolio.ratelimit.db.select")
@patch("portfolio.ratelimit.db.upsert")
def test_check_and_increment_ip_no_prior_row(mock_upsert, mock_select):
    mock_select.return_value = []
    status = check_and_increment_ip("hashval")
    assert status.allowed is True
    assert status.remaining == IP_DAILY_LIMIT - 1
    mock_upsert.assert_called_once()


@patch("portfolio.ratelimit.db.select")
@patch("portfolio.ratelimit.db.upsert")
def test_byok_does_not_count_rpd(mock_upsert, mock_select):
    mock_select.return_value = [{"count": 100, "cap": DAILY_CAP_DEFAULT}]
    allowed, remaining = check_and_increment_rpd(num_calls=2, byok=True)
    assert allowed is True
    mock_upsert.assert_not_called()


@patch("portfolio.ratelimit.db.select")
@patch("portfolio.ratelimit.db.upsert")
def test_rpd_under_cap_increments(mock_upsert, mock_select):
    mock_select.return_value = [{"count": 100, "cap": DAILY_CAP_DEFAULT}]
    allowed, remaining = check_and_increment_rpd(num_calls=2, byok=False)
    assert allowed is True
    assert remaining == DAILY_CAP_DEFAULT - 102
    mock_upsert.assert_called_once()


@patch("portfolio.ratelimit.db.select")
@patch("portfolio.ratelimit.db.upsert")
def test_rpd_would_exceed_cap_blocks(mock_upsert, mock_select):
    mock_select.return_value = [{"count": DAILY_CAP_DEFAULT - 1, "cap": DAILY_CAP_DEFAULT}]
    allowed, _ = check_and_increment_rpd(num_calls=2, byok=False)
    assert allowed is False
    mock_upsert.assert_not_called()


@patch("portfolio.ratelimit.db.select")
def test_get_today_status(mock_select):
    mock_select.return_value = [{"count": 50, "cap": 240}]
    status = get_today_status()
    assert status["daily_used"] == 50
    assert status["daily_cap"] == 240
