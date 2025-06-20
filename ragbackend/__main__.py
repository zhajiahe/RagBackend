import uvicorn

uvicorn.run("ragbackend.server:APP", host="0.0.0.0", port=8080)
