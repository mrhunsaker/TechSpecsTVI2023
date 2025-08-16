#!/bin/bash

# Define your search terms here
search_terms=(

)

# Directory to search
search_dir="./Chapters"

# Output file
output_file="snipehunt_results.csv"

# Write header to CSV
echo '"SearchTerm","Filename","LineNumber","LineContent"' > "$output_file"

# Loop over each term and search
for term in "${search_terms[@]}"; do
  # Use grep and process each match
  grep -rnw "$search_dir" -e "$term" | while IFS=: read -r file line content; do
    # Escape quotes in line content
    safe_content=$(echo "$content" | sed 's/"/""/g')
    echo "\"$term\",\"$file\",\"$line\",\"$safe_content\"" >> "$output_file"
  done
done

echo "✅ Results written to $output_file"
