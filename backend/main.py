from fastapi import FastAPI

app = FastAPI(
    title="Monitor de Editais API",
    description="API para o MVP da plataforma Monitor de Editais",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {"message": "Monitor de Editais API is running"}
