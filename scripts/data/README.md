# CSV Import Data Files

This directory contains CSV files for bulk importing records into InvenioRDM.

## Quick Start

```bash
# From the project root directory
make scripts-import CSV='data/sample_records.csv'
```

## CSV File Format

### Required Columns

| Column     | Description                            | Example                                                |
| ---------- | -------------------------------------- | ------------------------------------------------------ |
| `title`    | Record title                           | `"Climate Change Impact Dataset"`                      |
| `creators` | Creator information (see format below) | `"Maria Rossi;0000-0001-2345-6789;University of Rome"` |

### Optional Columns

| Column             | Description                           | Default               | Example                                      |
| ------------------ | ------------------------------------- | --------------------- | -------------------------------------------- |
| `record_id`        | Existing record ID for updates        | (empty - creates new) | `"abcd-1234"`                                |
| `description`      | Record description                    | (empty)               | `"A comprehensive dataset..."`               |
| `resource_type`    | Type of resource                      | `dataset`             | `dataset`, `publication-article`, `software` |
| `publication_date` | Publication date                      | Today's date          | `2024-01-15`                                 |
| `access_record`    | Record access level                   | `public`              | `public`, `restricted`                       |
| `access_files`     | Files access level                    | `public`              | `public`, `restricted`                       |
| `file_paths`       | Files to upload (semicolon-separated) | (empty)               | `/path/file1.csv;/path/file2.txt`            |
| `publish`          | Publish immediately                   | `no`                  | `yes`, `no`                                  |

## Creators Format

Creators should be specified in this format:

```
"Given Family; ORCID; Affiliation | Given2 Family2; ORCID2; Affiliation2"
```

### Components

1. **Name** (required): Given name(s) followed by family name

   - Example: `"Maria Rossi"` or `"John Peter Doe"`

2. **ORCID** (optional): ORCID identifier

   - Example: `"0000-0001-2345-6789"`
   - Leave empty if not available: `"Maria Rossi;;University"`

3. **Affiliation** (optional): Institution or organization
   - Example: `"University of Rome"`

### Multiple Creators

Use the pipe symbol `|` to separate multiple creators:

```
"Alice Smith;0000-0001-1111-1111;MIT | Bob Johnson;0000-0002-2222-2222;Stanford"
```

### Examples

```csv
# Single creator with all fields
"John Doe;0000-0001-2345-6789;University of Example"

# Single creator without ORCID
"Jane Smith;;Harvard University"

# Single creator with only name
"Robert Brown"

# Multiple creators with mixed information
"Alice White;0000-0001-1111-1111;MIT | Bob Green;;Stanford | Carol Blue;0000-0003-3333-3333;"
```

## Resource Types

Common resource types in InvenioRDM:

| Type                          | Description            |
| ----------------------------- | ---------------------- |
| `dataset`                     | Research dataset       |
| `publication-article`         | Journal article        |
| `publication-book`            | Book                   |
| `publication-section`         | Book chapter           |
| `publication-conferencepaper` | Conference paper       |
| `publication-thesis`          | Thesis or dissertation |
| `publication-report`          | Technical report       |
| `software`                    | Software package       |
| `image-photo`                 | Photograph             |
| `image-figure`                | Figure or diagram      |
| `video`                       | Video content          |
| `other`                       | Other resource type    |

For a complete list, check your InvenioRDM instance vocabularies.

## Access Levels

| Level        | Description                             |
| ------------ | --------------------------------------- |
| `public`     | Accessible to everyone                  |
| `restricted` | Restricted access (requires permission) |

You can set different access levels for the record metadata and the files:

- `access_record`: Controls who can see the metadata
- `access_files`: Controls who can download the files

## File Paths

Specify local file paths to upload to the record. Multiple files should be separated by semicolons:

```csv
file_paths
"/data/dataset.csv;/data/readme.txt;/data/analysis.py"
```

**Important**: File paths should be:

- Absolute paths or relative to the container's working directory
- Accessible from within the Docker container
- Properly escaped if they contain special characters

To upload files from your local machine, you may need to:

1. Place them in a directory that's mounted to the container
2. Use absolute paths that the container can access

## Complete Example

Here's a complete CSV file with various record types:

```csv
title,description,creators,resource_type,publication_date,access_record,access_files,file_paths,publish
"Climate Change Impact Dataset","A comprehensive dataset analyzing climate change impacts on agricultural productivity in Mediterranean regions","Maria Rossi;0000-0001-2345-6789;University of Rome | Giovanni Bianchi;;CNR",dataset,2024-01-15,public,public,,no
"AI Model Training Results","Results from training a deep learning model for image classification","Alice Smith;0000-0002-3456-7890;MIT | Bob Johnson;0000-0003-4567-8901;Stanford University",publication-computationalnotebook,2024-02-20,public,public,,yes
"Survey Data: European Research Trends","Survey responses from 5000 researchers across Europe","Francesco Verdi;;University of Florence | Emma White;0000-0004-5678-9012;Oxford",dataset,2024-03-10,public,restricted,,no
"Open Source Software Package","A Python package for statistical analysis","John Doe;0000-0005-6789-0123;Independent",software,2024-04-05,public,public,,yes
```

## Import Options

### Dry Run Mode

Test your CSV without creating records:

```bash
make scripts-import CSV='data/my_records.csv' OPTS='--dry-run'
```

This will:

- Validate the CSV structure
- Check required fields
- Parse all data
- Show what would be created
- Not create any actual records

### Skip Errors

Continue processing even if some records fail:

```bash
make scripts-import CSV='data/my_records.csv' OPTS='--skip-errors'
```

### Verbose Output

Show detailed information for each record:

```bash
make scripts-import CSV='data/my_records.csv' OPTS='--verbose'
```

### Combined Options

You can combine multiple options:

```bash
make scripts-import CSV='data/my_records.csv' OPTS='--dry-run --verbose'
make scripts-import CSV='data/my_records.csv' OPTS='--skip-errors --verbose'
```

## Update Existing Records

To update an existing record, include the `record_id` column:

```csv
record_id,title,description,creators,publication_date
"abcd-1234","Updated Title","Updated description","John Doe;;MIT",2024-06-15
```

The script will:

1. Check if the record exists
2. If it exists, create a new draft version and update it
3. If it doesn't exist, create a new record

## Publishing Records

Control whether records are published immediately:

```csv
title,creators,publish
"Draft Record","John Doe",no
"Published Record","Jane Smith",yes
```

- `publish=yes`: Record is published immediately after creation
- `publish=no` or empty: Record is saved as a draft

## Tips and Best Practices

1. **Test First**: Always use `--dry-run` mode first to validate your CSV
2. **Use Verbose Mode**: Use `--verbose` to see detailed processing information
3. **Handle Errors**: Use `--skip-errors` for large imports to continue despite individual failures
4. **Start Small**: Test with a few records before importing hundreds
5. **Backup Data**: Keep a copy of your CSV files
6. **Use UTF-8 Encoding**: Ensure your CSV file is UTF-8 encoded for international characters
7. **Quote Fields**: Quote fields that contain commas, semicolons, or special characters
8. **Validate ORCIDs**: Ensure ORCID identifiers are in the correct format (0000-0000-0000-0000)

## Troubleshooting

### Common Errors

**Missing Required Columns**

```
❌ Missing required columns: {'title', 'creators'}
```

→ Ensure your CSV has `title` and `creators` columns

**Invalid Creator Format**

```
⚠️ Skipping invalid creator name: X
```

→ Creator names must have at least a given name and family name

**File Not Found**

```
⚠️ File not found: /path/to/file.csv
```

→ Check that file paths are correct and accessible from the container

**Connection Error**

```
❌ Failed to connect to InvenioRDM
```

→ Ensure InvenioRDM is running (`make up`) and the environment is configured (`make scripts-setup-env`)

### Validation Tips

Before importing, validate your CSV:

```bash
# Check CSV structure
head -n 2 data/my_records.csv

# Count records
wc -l data/my_records.csv

# Test with dry-run
make scripts-import CSV='data/my_records.csv' OPTS='--dry-run --verbose'
```

## Examples Directory

See `sample_records.csv` for a working example with various record types and configurations.
