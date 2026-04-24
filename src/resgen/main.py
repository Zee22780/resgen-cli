import typer
from dotenv import load_dotenv

load_dotenv()

app = typer.Typer()

@app.command()
def hello():
    """Test command to verify setup."""
    typer.echo("resgen-cli is set up and ready!")

if __name__ == "__main__":
    app()
