from Implementierungen.ssh_with_parameters import create_ssh_client


def test_create_ssh_client():
    result = create_ssh_client()
    assert result == True
