import { migratePlatformDatabase } from "../migrate.mjs";

try {
  const result = await migratePlatformDatabase();
  process.stdout.write(`bairui platform database ${result.schema_version} is ${result.status}\n`);
} catch (error) {
  process.stderr.write(`${error.message}\n`);
  process.exitCode = 1;
}
