import crypto from "node:crypto";
import { createReadStream, createWriteStream } from "node:fs";
import { readdir, stat } from "node:fs/promises";
import { basename, join } from "node:path";
import { createGzip } from "node:zlib";

function requireString(options, key) {
  const value = options[key];
  if (typeof value !== "string" || value.trim() === "") {
    throw new Error(`${key} is required`);
  }
  return value.trim();
}

function padOctal(value, length) {
  const text = value.toString(8);
  return text.padStart(length - 1, "0") + "\0";
}

function writeString(buffer, offset, length, value) {
  buffer.write(String(value).slice(0, length), offset, length, "utf8");
}

function tarHeader(name, size) {
  const header = Buffer.alloc(512, 0);
  writeString(header, 0, 100, name);
  writeString(header, 100, 8, "0000644\0");
  writeString(header, 108, 8, "0000000\0");
  writeString(header, 116, 8, "0000000\0");
  writeString(header, 124, 12, padOctal(size, 12));
  writeString(header, 136, 12, "00000000000\0");
  writeString(header, 148, 8, "        ");
  writeString(header, 156, 1, "0");
  writeString(header, 257, 6, "ustar\0");
  writeString(header, 263, 2, "00");

  let checksum = 0;
  for (const byte of header) {
    checksum += byte;
  }
  writeString(header, 148, 8, padOctal(checksum, 8));
  return header;
}

async function listRegularFiles(inputDir) {
  const entries = await readdir(inputDir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    if (!entry.isFile()) {
      continue;
    }
    const path = join(inputDir, entry.name);
    const info = await stat(path);
    files.push({ name: entry.name, path, size: info.size });
  }
  return files.sort((left, right) => left.name.localeCompare(right.name));
}

function pipeFile(path, output) {
  return new Promise((resolve, reject) => {
    const stream = createReadStream(path);
    stream.on("error", reject);
    stream.on("end", resolve);
    stream.pipe(output, { end: false });
  });
}

function writeBuffer(output, buffer) {
  return new Promise((resolve, reject) => {
    output.write(buffer, (error) => {
      if (error) {
        reject(error);
      } else {
        resolve();
      }
    });
  });
}

async function writeTar(inputDir, output) {
  const root = basename(inputDir).replace(/[^A-Za-z0-9._-]/g, "-") || "delivery";
  const files = await listRegularFiles(inputDir);
  for (const file of files) {
    const tarName = `${root}/${file.name}`;
    await writeBuffer(output, tarHeader(tarName, file.size));
    await pipeFile(file.path, output);
    const padding = (512 - (file.size % 512)) % 512;
    if (padding > 0) {
      await writeBuffer(output, Buffer.alloc(padding, 0));
    }
  }
  await writeBuffer(output, Buffer.alloc(1024, 0));
  return files.map((file) => file.name);
}

export async function archiveDeliveryPackage(options) {
  const inputDir = requireString(options, "inputDir");
  const outputFile = requireString(options, "outputFile");
  const hash = crypto.createHash("sha256");
  const fileOutput = createWriteStream(outputFile);
  const gzip = createGzip({ mtime: new Date(0) });

  gzip.on("data", (chunk) => hash.update(chunk));
  gzip.pipe(fileOutput);

  const files = await writeTar(inputDir, gzip);
  gzip.end();

  await new Promise((resolve, reject) => {
    fileOutput.on("finish", resolve);
    fileOutput.on("error", reject);
    gzip.on("error", reject);
  });

  return {
    archive: outputFile,
    sha256: hash.digest("hex"),
    files
  };
}
