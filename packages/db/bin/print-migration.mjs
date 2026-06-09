import { buildMigrationSql } from "../schema.mjs";

process.stdout.write(buildMigrationSql());
