#!/bin/bash
set -e
echo "Copying source from frontend/..."
cp -r frontend/src .
cp -r frontend/public .
cp frontend/tsconfig.json .
cp frontend/tailwind.config.ts .
cp frontend/postcss.config.js .
cp frontend/next-env.d.ts .
echo "Running next build..."
next build
