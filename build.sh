#!/bin/bash
set -e
echo "Copying source from frontend/..."
rm -rf src public
cp -r frontend/src .
cp -r frontend/public .
cp frontend/tsconfig.json .
cp frontend/tailwind.config.ts .
cp frontend/postcss.config.js .
cp frontend/next-env.d.ts .
echo "Running next build..."
if [ -x "./node_modules/.bin/next" ]; then
  ./node_modules/.bin/next build
elif [ -x "./frontend/node_modules/.bin/next" ]; then
  ./frontend/node_modules/.bin/next build
else
  npx next build
fi
