"""Lens.org Proxy API for downloading references and citations."""

import requests
from flask import Response, request
from flask.views import MethodView


class LensExportProxyAPIView(MethodView):
    """
    Proxy endpoint for Lens.org export API.

    This bypasses CORS restrictions by making the request server-side.

    Usage:
        GET /api/lens/export?type=references&lens_id=XXX-XXX-XXX-XXX-XXX
        GET /api/lens/export?type=citations&lens_id=XXX-XXX-XXX-XXX-XXX
    """

    def get(self):
        """Handle export request by proxying to Lens.org."""
        export_type = request.args.get("type", "references")
        lens_id = request.args.get("lens_id")

        if not lens_id:
            return {"error": "lens_id parameter is required"}, 400

        # Build the Lens.org URL based on export type
        # referenceId.must=XXX finds articles that have XXX in their references (articles citing XXX)
        if export_type == "references":
            # For references: we need articles that THIS article references
            # This requires a different approach - get the article's reference list
            url = f"https://www.lens.org/lens/export/scholar?q=&st=true&citingId.must={lens_id}"
        elif export_type == "citations":
            # For citations: articles that cite THIS article (have this article in their references)
            url = f"https://www.lens.org/lens/export/scholar?q=&st=true&referenceId.must={lens_id}"
        else:
            return {"error": "Invalid type. Use 'references' or 'citations'"}, 400

        # Build the payload
        payload = {
            "size": 1000,
            "from": 0,
            "sort": [
                {
                    "year_published": {"order": "desc"},
                    "date_published": {"missing": "_last", "order": "desc"},
                }
            ],
            "_source": {
                "includes": [
                    "author.display_name",
                    "author.orcid",
                    "conference.name",
                    "date_published",
                    "ids",
                    "end_page",
                    "has_abstract",
                    "has_affiliation",
                    "has_affiliation_ror",
                    "has_chemical",
                    "has_clinical_trial",
                    "has_field_of_study",
                    "has_full_text",
                    "has_funding",
                    "has_keyword",
                    "has_mesh_term",
                    "has_orcid",
                    "is_open_access",
                    "is_retracted",
                    "is_referenced_by_patent",
                    "is_referenced_by_scholarly",
                    "issue",
                    "lens_id_num",
                    "lens_id",
                    "publication_type",
                    "record_lens_id_num",
                    "record_lens_id",
                    "reference_count",
                    "referenced_by_count",
                    "referenced_by_patent_count",
                    "source.title",
                    "start_page",
                    "title",
                    "volume",
                    "year_published",
                ]
            },
            "highlight": {
                "type": "plain",
                "pre_tags": ['<span class="highlight">'],
                "post_tags": ["</span>"],
                "fields": {
                    "title": {"fragment_size": 500},
                    "fulltext": {},
                    "claim": {},
                    "description": {},
                    "abstract": {},
                },
                "number_of_fragments": 3,
            },
            "sortField": "year_published",
            "sortOrder": "DESC",
            "format": "CSV",
            "fields": [
                "LENS_ID",
                "TITLE",
                "DATE_PUBLISHED",
                "YEAR_PUBLISHED",
                "PUBLICATION_TYPE",
                "JOURNAL_TITLE",
                "JOURNAL_ISSN",
                "JOURNAL_PUBLISHER",
                "JOURNAL_COUNTRY",
                "AUTHORS",
                "ABSTRACT",
                "VOLUME",
                "ISSUE",
                "START_PAGE",
                "END_PAGE",
                "FIELDS_OF_STUDY",
                "KEYWORDS",
                "MESH_TERMS",
                "CHEMICALS",
                "FUNDING",
                "SOURCE_URLS",
                "EXTERNAL_URL",
                "PMID",
                "DOI",
                "MAG_ID",
                "PMCID",
                "REFERENCED_BY_PATENT_COUNT",
                "REFERENCES_LENS_IDS",
                "REFERENCED_BY_COUNT",
                "IS_OPEN_ACCESS",
                "OPEN_ACCESS_LICENSE",
                "OPEN_ACCESS_COLOUR",
            ],
            "filename": f"lens-{export_type}-export",
            "async": False,
        }

        try:
            # Make the request to Lens.org
            response = requests.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "*/*",
                    "User-Agent": "Mozilla/5.0 (compatible; UNESCO-OpenScience/1.0)",
                },
                timeout=180,
                stream=True,  # Stream large responses
            )

            if response.status_code == 200:
                try:
                    # Read response in chunks for better handling of large payloads
                    chunks = []
                    received_bytes = 0
                    chunk_size = 8192  # 8KB chunks
                    
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            chunks.append(chunk)
                            received_bytes += len(chunk)
                    
                    content = b''.join(chunks)
                    
                    # Return the CSV file
                    return Response(
                        content,
                        mimetype="text/csv",
                        headers={
                            "Content-Disposition": f"attachment; filename=lens-{export_type}-{lens_id}.csv"
                        },
                    )
                except Exception as e:
                    # Handle content reading errors (truncated/incomplete response)
                    expected_size = response.headers.get('content-length', 'unknown')
                    return {
                        "error": "Failed to read complete response from Lens.org",
                        "error_type": "incomplete_response",
                        "details": str(e),
                        "expected_size": expected_size,
                        "received_bytes": received_bytes if 'received_bytes' in dir() else 0,
                        "suggestion": "The response may be too large or incomplete. Try reducing the request size."
                    }, 502
            else:
                return {
                    "error": f"Lens.org returned status {response.status_code}",
                    "detail": response.text[:500] if response.text else "No details",
                }, response.status_code

        except requests.exceptions.Timeout:
            # Use custom timeout status code (524 for external service timeout)
            from flask import current_app
            status_code = current_app.config.get('GATEWAY_TIMEOUT_STATUS_CODE', 504)
            return {
                "error": "Request to Lens.org timed out",
                "error_type": "external_timeout",
                "retry_after": 60
            }, status_code
        except requests.exceptions.ChunkedEncodingError as e:
            # Handle incomplete chunk errors (common with large payloads)
            return {
                "error": "Incomplete response from Lens.org",
                "error_type": "chunked_encoding_error",
                "details": str(e),
                "suggestion": "The response was truncated. Try reducing the size parameter."
            }, 502
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to connect to Lens.org: {str(e)}"}, 502
