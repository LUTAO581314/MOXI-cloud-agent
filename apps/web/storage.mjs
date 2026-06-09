import { createPgPool, createPostgresRegistryStorage } from "./postgres-registry.mjs";
import { createJsonRegistryStorage } from "./server-registry.mjs";

export async function createRegistryStorage(config) {
  if (config.databaseUrl) {
    const pool = await createPgPool(config.databaseUrl);
    return createPostgresRegistryStorage(pool);
  }
  return createJsonRegistryStorage({ registryPath: config.registryPath });
}
