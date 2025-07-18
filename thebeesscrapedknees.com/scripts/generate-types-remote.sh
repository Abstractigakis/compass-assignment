#!/bin/bash

# Load environment variables from .env.local
if [ -f .env.local ]; then
    export $(cat .env.local | grep -v '^#' | xargs)
fi

# Check if NEXT_PUBLIC_PROJECT_REF_ID is set
if [ -z "$NEXT_PUBLIC_PROJECT_REF_ID" ]; then
    echo "Error: NEXT_PUBLIC_PROJECT_REF_ID not found in .env.local"
    exit 1
fi

echo "Generating types for project: $NEXT_PUBLIC_PROJECT_REF_ID"

# Generate types from remote Supabase project
npx supabase gen types typescript --project-id "$NEXT_PUBLIC_PROJECT_REF_ID" --schema public >./lib/supabase/db.types.ts

echo "Types generated successfully!"
