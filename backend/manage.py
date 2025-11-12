import os
from flask import Flask
import click
from dotenv import load_dotenv
from constants.db_collections import MongoCollections as mc
from migrations.migrate_json_data import migrate_json_data
from migrations.migrate_admin_creds import migrate_admin_creds

load_dotenv()

# Migration Usage Examples:
# flask --app manage.py migrate music.json --reset
# flask --app manage.py migrate all --reset
# flask --app manage.py migrate users --reset

MIGRATIONS = {
    "gallery.json": mc.GALLERY,
    "music.json": mc.MUSIC,
    "vlog.json": mc.VIDEO,
    "project.json": mc.PROJECT,
}

def create_app():
    app = Flask(__name__)

    # Load configs (from .env)
    app.config["MONGO_URI"] = os.getenv("MONGO_URI")
    app.config["MONGO_DB"] = os.getenv("MONGO_DB")

    @app.cli.command("migrate")
    @click.argument("name", required=False)  # e.g., music.json / all / users
    @click.option("--reset", is_flag=True, help="Clear collection before inserting")
    def migrate_command(name, reset):
        if name == "all":
            # Run all JSON migrations
            for json_file, collection in MIGRATIONS.items():
                migrate_json_data(json_file, collection, reset)
                click.echo(f"✅ Migrated {json_file} into '{collection}' collection")

            # Run admin migration
            migrate_admin_creds(
                username=os.getenv("ADMIN_USERNAME", "admin"),
                password=os.getenv("ADMIN_PASSWORD", "password"),
                reset=reset
            )
            click.echo("✅ Migrated admin credentials into 'users' collection")
            click.echo("🎉 All migrations completed!")

        elif name in MIGRATIONS:
            migrate_json_data(name, MIGRATIONS[name], reset)
            click.echo(f"✅ Migrated {name} into '{MIGRATIONS[name]}' collection")

        elif name == "users":
            migrate_admin_creds(
                mc.USERS,
                username=os.getenv("ADMIN_USERNAME", "admin"),
                password=os.getenv("ADMIN_PASSWORD", "password"),
                reset=reset
            )
            click.echo("✅ Migrated admin credentials into 'users' collection")

        else:
            click.echo(f"❌ Unknown migration: {name}. Choose from {list(MIGRATIONS.keys())} + 'users' or 'all'.")

    return app

app = create_app()
