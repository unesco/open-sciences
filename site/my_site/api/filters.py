"""Filter backends for search API.

Inspired by Django REST Framework and django-filter patterns.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from invenio_search import current_search_client


class BaseFilterBackend(ABC):
    """Base class for filter backends."""

    @abstractmethod
    def get_field_name(self) -> str:
        """Return the OpenSearch field name to aggregate on."""
        pass

    @abstractmethod
    def get_filter_key(self) -> str:
        """Return the filter key used in URL (e.g., 'country', 'funding')."""
        pass

    def get_index_name(self) -> str:
        """Return the OpenSearch index name. Override if needed."""
        return "my-site-rdmrecords-records"

    def get_aggregation_size(self) -> int:
        """Return the maximum number of aggregation buckets. Override if needed."""
        return 100

    def get_aggregation_order(self) -> Dict[str, str]:
        """Return the aggregation order. Override if needed."""
        return {"_key": "asc"}

    def build_query(self, search_term: Optional[str] = None) -> Dict[str, Any]:
        """Build the OpenSearch query with aggregations."""
        return {
            "size": 0,  # We don't need the actual documents
            "aggs": {
                f"unique_{self.get_filter_key()}": {
                    "terms": {
                        "field": self.get_field_name(),
                        "size": self.get_aggregation_size(),
                        "order": self.get_aggregation_order(),
                    }
                }
            },
        }

    def filter_results(
        self, buckets: List[Dict], search_term: Optional[str]
    ) -> List[Dict]:
        """Filter aggregation results by search term."""
        results = []
        for bucket in buckets:
            key = bucket["key"]
            # Filter by search term if provided
            if not search_term or search_term.lower() in key.lower():
                results.append(
                    {
                        "name": key,
                        "value": key,
                        "text": key,
                        "doc_count": bucket["doc_count"],
                    }
                )
        return results

    def execute(self, search_term: Optional[str] = None) -> List[Dict]:
        """Execute the search and return filtered results."""
        try:
            query = self.build_query(search_term)
            result = current_search_client.search(
                index=self.get_index_name(), body=query
            )

            # Extract buckets from aggregations
            agg_key = f"unique_{self.get_filter_key()}"
            buckets = []
            if "aggregations" in result and agg_key in result["aggregations"]:
                buckets = result["aggregations"][agg_key]["buckets"]

            return self.filter_results(buckets, search_term)

        except Exception as e:
            # Log error and return empty results
            print(f"Error in {self.__class__.__name__}: {str(e)}")
            return []


class CountryFilterBackend(BaseFilterBackend):
    """Filter backend for publication countries."""

    def get_field_name(self) -> str:
        return "custom_fields.publication:country"

    def get_filter_key(self) -> str:
        return "country"


class FundingOrgFilterBackend(BaseFilterBackend):
    """Filter backend for funding organizations.

    Note: funder.name is a text field (not keyword), so we cannot use
    standard aggregations. We fetch documents and aggregate in Python.
    """

    def get_field_name(self) -> str:
        return "metadata.funding.funder.name"

    def get_filter_key(self) -> str:
        return "funding"

    def execute(self, search_term: str = None) -> List[Dict]:
        """
        Override execute for funding - text field requires different approach.
        We fetch ALL records and filter/aggregate funding organizations in Python.
        This allows for proper substring matching that works correctly.
        """
        try:
            # Build query - fetch all records with funding
            query_body = {
                "size": 1000,  # Fetch more records to get comprehensive funding data
                "_source": ["metadata.funding"],
                "query": {"exists": {"field": "metadata.funding"}},
            }

            # Execute search
            result = current_search_client.search(
                index=self.get_index_name(), body=query_body
            )

            # Aggregate funding organizations manually
            org_counts = {}
            for hit in result.get("hits", {}).get("hits", []):
                funding_list = (
                    hit.get("_source", {}).get("metadata", {}).get("funding", [])
                )
                for funding_item in funding_list:
                    funder_name = funding_item.get("funder", {}).get("name")
                    if funder_name:
                        org_counts[funder_name] = org_counts.get(funder_name, 0) + 1

            # Filter by search term (case-insensitive substring match)
            if search_term:
                search_lower = search_term.lower()
                org_counts = {
                    name: count
                    for name, count in org_counts.items()
                    if search_lower in name.lower()
                }

            # Convert to results format and sort alphabetically
            results = []
            for org_name, count in org_counts.items():
                results.append(
                    {
                        "value": org_name,
                        "text": org_name,
                        "name": org_name,
                        "doc_count": count,
                    }
                )

            results.sort(key=lambda x: x["name"].lower())

            # Limit to max size
            return results[: self.get_aggregation_size()]

        except Exception as e:
            print(f"Error in FundingOrgFilterBackend: {str(e)}")
            return []


class AuthorFilterBackend(BaseFilterBackend):
    """Filter backend for author names.

    Note: person_or_org.name is a text field, so we fetch records
    and aggregate authors in Python for proper substring matching.
    """

    def get_field_name(self) -> str:
        return "metadata.creators.person_or_org.name"

    def get_filter_key(self) -> str:
        return "author"

    def execute(self, search_term: str = None) -> List[Dict]:
        """
        Override execute for authors - text field requires different approach.
        We fetch ALL records and filter/aggregate author names in Python.
        """
        try:
            # Build query - fetch all records with creators
            query_body = {
                "size": 1000,
                "_source": ["metadata.creators"],
                "query": {"exists": {"field": "metadata.creators"}},
            }

            # Execute search
            result = current_search_client.search(
                index=self.get_index_name(), body=query_body
            )

            # Aggregate author names manually
            author_counts = {}
            for hit in result.get("hits", {}).get("hits", []):
                creators_list = (
                    hit.get("_source", {}).get("metadata", {}).get("creators", [])
                )
                for creator in creators_list:
                    author_name = creator.get("person_or_org", {}).get("name")
                    if author_name:
                        author_counts[author_name] = (
                            author_counts.get(author_name, 0) + 1
                        )

            # Filter by search term (case-insensitive substring match)
            if search_term:
                search_lower = search_term.lower()
                author_counts = {
                    name: count
                    for name, count in author_counts.items()
                    if search_lower in name.lower()
                }

            # Convert to results format and sort alphabetically
            results = []
            for author_name, count in author_counts.items():
                results.append(
                    {
                        "value": author_name,
                        "text": author_name,
                        "name": author_name,
                        "doc_count": count,
                    }
                )

            results.sort(key=lambda x: x["name"].lower())

            # Limit to max size
            return results[: self.get_aggregation_size()]

        except Exception as e:
            print(f"Error in AuthorFilterBackend: {str(e)}")
            return []


class SubjectFilterBackend(BaseFilterBackend):
    """Filter backend for subjects/keywords.

    Note: subjects.subject is a text field, so we fetch records
    and aggregate subjects in Python for proper substring matching.
    """

    def get_field_name(self) -> str:
        return "metadata.subjects.subject"

    def get_filter_key(self) -> str:
        return "subject"

    def execute(self, search_term: str = None) -> List[Dict]:
        """
        Override execute for subjects - text field requires different approach.
        We fetch ALL records and filter/aggregate subjects in Python.
        """
        try:
            # Build query - fetch all records with subjects
            query_body = {
                "size": 1000,
                "_source": ["metadata.subjects"],
                "query": {"exists": {"field": "metadata.subjects"}},
            }

            # Execute search
            result = current_search_client.search(
                index=self.get_index_name(), body=query_body
            )

            # Aggregate subjects manually
            subject_counts = {}
            for hit in result.get("hits", {}).get("hits", []):
                subjects_list = (
                    hit.get("_source", {}).get("metadata", {}).get("subjects", [])
                )
                for subject_obj in subjects_list:
                    subject = subject_obj.get("subject")
                    if subject:
                        subject_counts[subject] = subject_counts.get(subject, 0) + 1

            # Filter by search term (case-insensitive substring match)
            if search_term:
                search_lower = search_term.lower()
                subject_counts = {
                    name: count
                    for name, count in subject_counts.items()
                    if search_lower in name.lower()
                }

            # Convert to results format and sort alphabetically
            results = []
            for subject, count in subject_counts.items():
                results.append(
                    {
                        "value": subject,
                        "text": subject,
                        "name": subject,
                        "doc_count": count,
                    }
                )

            results.sort(key=lambda x: x["name"].lower())

            # Limit to max size
            return results[: self.get_aggregation_size()]

        except Exception as e:
            print(f"Error in SubjectFilterBackend: {str(e)}")
            return []


class AffiliationFilterBackend(BaseFilterBackend):
    """Filter backend for affiliations.

    Note: affiliations.name is a text field, so we fetch records
    and aggregate affiliations in Python for proper substring matching.
    """

    def get_field_name(self) -> str:
        return "metadata.creators.affiliations.name"

    def get_filter_key(self) -> str:
        return "affiliation"

    def execute(self, search_term: str = None) -> List[Dict]:
        """
        Override execute for affiliations - text field requires different approach.
        We fetch ALL records and filter/aggregate affiliations in Python.
        """
        try:
            # Build query - fetch all records with creators
            query_body = {
                "size": 1000,
                "_source": ["metadata.creators"],
                "query": {"exists": {"field": "metadata.creators"}},
            }

            # Execute search
            result = current_search_client.search(
                index=self.get_index_name(), body=query_body
            )

            # Aggregate affiliations manually
            affiliation_counts = {}
            for hit in result.get("hits", {}).get("hits", []):
                creators_list = (
                    hit.get("_source", {}).get("metadata", {}).get("creators", [])
                )
                for creator in creators_list:
                    affiliations = creator.get("affiliations", [])
                    for affiliation in affiliations:
                        name = affiliation.get("name")
                        if name:
                            affiliation_counts[name] = (
                                affiliation_counts.get(name, 0) + 1
                            )

            # Filter by search term (case-insensitive substring match)
            if search_term:
                search_lower = search_term.lower()
                affiliation_counts = {
                    name: count
                    for name, count in affiliation_counts.items()
                    if search_lower in name.lower()
                }

            # Convert to results format and sort alphabetically
            results = []
            for name, count in affiliation_counts.items():
                results.append(
                    {
                        "value": name,
                        "text": name,
                        "name": name,
                        "doc_count": count,
                    }
                )

            results.sort(key=lambda x: x["name"].lower())

            # Limit to max size
            return results[: self.get_aggregation_size()]

        except Exception as e:
            print(f"Error in AffiliationFilterBackend: {str(e)}")
            return []


class PublicationYearFilterBackend(BaseFilterBackend):
    """Filter backend for publication years."""

    def get_field_name(self) -> str:
        return "metadata.publication_date"

    def get_filter_key(self) -> str:
        return "year"

    def get_aggregation_order(self) -> Dict[str, str]:
        """Order years in descending order."""
        return {"_key": "desc"}

    def filter_results(
        self, buckets: List[Dict], search_term: Optional[str]
    ) -> List[Dict]:
        """Extract year from date and filter."""
        results = []
        for bucket in buckets:
            # Extract year from date string (format: YYYY-MM-DD)
            date_str = (
                bucket["key_as_string"]
                if "key_as_string" in bucket
                else str(bucket["key"])
            )
            year = date_str.split("-")[0]

            # Filter by search term if provided
            if not search_term or search_term in year:
                results.append(
                    {
                        "name": year,
                        "value": year,
                        "text": year,
                        "doc_count": bucket["doc_count"],
                    }
                )
        return results


class ResourceTypeFilterBackend(BaseFilterBackend):
    """Filter backend for resource types."""

    def get_field_name(self) -> str:
        return "metadata.resource_type.id"

    def get_filter_key(self) -> str:
        return "resource_type"


# Registry of available filter backends
FILTER_BACKENDS_REGISTRY = {
    "affiliation": AffiliationFilterBackend,
    "author": AuthorFilterBackend,
    "country": CountryFilterBackend,
    "funding": FundingOrgFilterBackend,
    "subject": SubjectFilterBackend,
    "year": PublicationYearFilterBackend,
    "resource_type": ResourceTypeFilterBackend,
}


def get_filter_backend(filter_key: str) -> Optional[BaseFilterBackend]:
    """
    Get a filter backend instance by key.

    Args:
        filter_key: The filter key (e.g., 'country', 'funding')

    Returns:
        Filter backend instance or None if not found
    """
    backend_class = FILTER_BACKENDS_REGISTRY.get(filter_key)
    if backend_class:
        return backend_class()
    return None
