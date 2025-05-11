from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import UUID

from httpx import ASGITransport, AsyncClient

from langconnect.database import get_vectorstore
from langconnect.database.connection import POSTGRES_DB, POSTGRES_HOST
from langconnect.server import APP

USER_1_HEADERS = {
    "Authorization": "Bearer user1",
}

USER_2_HEADERS = {
    "Authorization": "Bearer user2",
}

NO_SUCH_USER_HEADERS = {
    "Authorization": "Bearer no_such_user",
}


def reset_db() -> None:
    """Hacky code to initialize the database. This needs to be fixed."""
    if POSTGRES_DB != "langchain_test":
        raise AssertionError(
            "Attempting to run unit tests with a non-test database. "
            "Please set the database to 'test' before running tests."
        )
    if POSTGRES_HOST != "localhost":
        raise AssertionError(
            "Attempting to run unit tests with a non-localhost database. "
            "Please set the host to 'localhost' before running tests."
        )
    vectorstore = get_vectorstore()
    # Drop table
    vectorstore.drop_tables()
    # Re-create
    vectorstore.__post_init__()


@asynccontextmanager
async def get_async_test_client() -> AsyncGenerator[AsyncClient, None]:
    """Get an async client."""
    url = "http://localhost:9999"
    transport = ASGITransport(
        app=APP,
        raise_app_exceptions=True,
    )
    reset_db()
    async_client = AsyncClient(base_url=url, transport=transport)
    try:
        yield async_client
    finally:
        await async_client.aclose()


async def test_health() -> None:
    """Test the health check endpoint."""
    async with get_async_test_client() as client:
        response = await client.get("/health")
        response.raise_for_status()
        assert response.json() == {"status": "ok"}


async def test_create_and_get_collection() -> None:
    """Test creating and retrieving a collection."""
    async with get_async_test_client() as client:
        payload = {"name": "test_collection", "metadata": {"purpose": "unit-test"}}
        response = await client.post(
            "/collections", json=payload, headers=USER_1_HEADERS
        )
        assert response.status_code == 201, (
            f"Failed with error message: {response.text}"
        )
        data = response.json()
        assert data["name"] == "test_collection"
        assert isinstance(UUID(data["uuid"]), UUID)

        # Get collection by name
        get_response = await client.get(
            f"/collections/{data['name']}", headers=USER_1_HEADERS
        )
        assert get_response.status_code == 200
        assert get_response.json()["uuid"] == data["uuid"]


async def test_create_and_list_collection() -> None:
    """Test creating and listing a collection."""
    async with get_async_test_client() as client:
        payload = {"name": "test_collection", "metadata": {"purpose": "unit-test"}}
        response = await client.post(
            "/collections", json=payload, headers=USER_1_HEADERS
        )
        assert response.status_code == 201, (
            f"Failed with error message: {response.text}"
        )
        data = response.json()
        assert data["name"] == "test_collection"
        assert isinstance(UUID(data["uuid"]), UUID)

        # List collections
        list_response = await client.get("/collections", headers=USER_1_HEADERS)
        assert list_response.status_code == 200
        collections = list_response.json()
        assert len(collections) > 0
        assert any(c["name"] == "test_collection" for c in collections)


async def test_create_collection_conflict() -> None:
    """Creating a collection twice should return 409."""
    async with get_async_test_client() as client:
        payload = {"name": "dup_collection", "metadata": {"foo": "bar"}}
        # first create
        r1 = await client.post("/collections", json=payload, headers=USER_1_HEADERS)
        assert r1.status_code == 201

        # second create with same name
        r2 = await client.post("/collections", json=payload, headers=USER_1_HEADERS)
        assert r2.status_code == 409
        assert "already exists" in r2.json()["detail"]


async def test_create_collection_requires_auth() -> None:
    """POST /collections without a valid token should be 401."""
    async with get_async_test_client() as client:
        payload = {"name": "no_auth", "metadata": {}}
        r = await client.post("/collections", json=payload)
        assert r.status_code == 401

        r2 = await client.post(
            "/collections", json=payload, headers=NO_SUCH_USER_HEADERS
        )
        assert r2.status_code == 401


async def test_get_nonexistent_collection() -> None:
    """GET a collection that doesn't exist should be 404."""
    async with get_async_test_client() as client:
        r = await client.get("/collections/nonexistent")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"].lower()


async def test_delete_collection_and_nonexistent() -> None:
    """DELETE removes an existing collection and returns 404 on missing."""
    async with get_async_test_client() as client:
        # create first
        payload = {"name": "to_delete", "metadata": {}}
        r1 = await client.post("/collections", json=payload, headers=USER_1_HEADERS)
        assert r1.status_code == 201

        # delete it
        r2 = await client.delete("/collections/to_delete")
        assert r2.status_code == 204

        # then GET should 404
        r3 = await client.get("/collections/to_delete")
        assert r3.status_code == 404

        # deleting again yields 404
        r4 = await client.delete("/collections/to_delete")
        assert r4.status_code == 404


async def test_update_collection_name_and_metadata() -> None:
    """PATCH should rename and/or update metadata properly."""
    async with get_async_test_client() as client:
        # create two collections
        await client.post(
            "/collections",
            json={"name": "colA", "metadata": {"a": 1}},
            headers=USER_1_HEADERS,
        )
        await client.post(
            "/collections",
            json={"name": "colB", "metadata": {"b": 2}},
            headers=USER_1_HEADERS,
        )

        # try renaming colA to colB (conflict)
        conflict = await client.patch(
            "/collections/colA",
            json={"name": "colB"},
        )
        assert conflict.status_code == 409

        # rename colA to colC with new metadata
        update = await client.patch(
            "/collections/colA",
            json={"name": "colC", "metadata": {"x": "y"}},
        )
        assert update.status_code == 200
        body = update.json()
        assert body["name"] == "colC"
        assert body["metadata"] == {"x": "y"}
        # ensure old name is gone
        get_old = await client.get("/collections/colA")
        assert get_old.status_code == 404
        # ensure new name works
        get_new = await client.get("/collections/colC")
        assert get_new.status_code == 200

        # update metadata only on colC
        meta_update = await client.patch(
            "/collections/colC",
            json={"metadata": {"foo": "bar"}},
        )
        assert meta_update.status_code == 200
        assert meta_update.json()["metadata"] == {"foo": "bar"}


async def test_update_nonexistent_collection() -> None:
    """PATCH a missing collection should return 404."""
    async with get_async_test_client() as client:
        r = await client.patch(
            "/collections/does_not_exist",
            json={"metadata": {"any": "thing"}},
        )
        assert r.status_code == 404


async def test_list_empty_and_multiple_collections() -> None:
    """Listing when empty and after multiple creates."""
    async with get_async_test_client() as client:
        # ensure database is empty
        empty = await client.get("/collections")
        assert empty.status_code == 200
        assert empty.json() == []

        # create several
        names = ["one", "two", "three"]
        for n in names:
            r = await client.post(
                "/collections", json={"name": n, "metadata": {}}, headers=USER_1_HEADERS
            )
            assert r.status_code == 201

        listed = await client.get("/collections")
        assert listed.status_code == 200
        got = [c["name"] for c in listed.json()]
        for n in names:
            assert n in got
