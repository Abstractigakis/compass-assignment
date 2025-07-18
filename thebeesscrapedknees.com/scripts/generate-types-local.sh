#!/bin/bash

echo "Generating types from local Supabase instance..."

# Generate types from local Supabase project
npx supabase gen types typescript --local --schema public >./lib/supabase/db.types.ts

echo "Local types generated successfully!"
