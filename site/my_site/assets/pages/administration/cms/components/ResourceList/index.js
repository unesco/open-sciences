/**
 * ResourceList Component
 * Displays available CMS resource types as elegant cards
 */

import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import {
  Card,
  Button,
  Loader,
  Message,
  Icon,
  Label,
  Header,
  Segment,
  Grid,
} from "semantic-ui-react";
import { useResourceCMSApi } from "../../hooks";

/**
 * ResourceList - Shows all available CMS resource types as cards
 */
export const ResourceList = ({ onSelectResource }) => {
  const { listResources, loading, error } = useResourceCMSApi();
  const [resources, setResources] = useState([]);

  // Fetch resources on mount
  useEffect(() => {
    const fetchResources = async () => {
      try {
        const result = await listResources();
        setResources(result.resources || []);
      } catch (err) {
        console.error("Error fetching resources:", err);
      }
    };

    fetchResources();
  }, [listResources]);

  // Get icon based on resource type
  const getResourceIcon = (resourceType) => {
    const icons = {
      header: "window maximize outline",
      footer: "window minimize outline",
      homepage_hero: "image outline",
      homepage_highlights: "star outline",
      homepage_partners: "handshake outline",
      homepage_infographics: "chart bar outline",
      privacy_policy: "shield alternate",
      plain_language_summary: "file text outline",
      static_page: "file alternate outline",
    };
    return icons[resourceType] || "file outline";
  };

  // Get color based on resource type category
  const getResourceColor = (resourceType) => {
    const colors = {
      header: "blue",
      footer: "blue",
      homepage_hero: "purple",
      homepage_highlights: "purple",
      homepage_partners: "purple",
      homepage_infographics: "purple",
      privacy_policy: "teal",
      plain_language_summary: "orange",
      static_page: "green",
    };
    return colors[resourceType] || "grey";
  };

  if (loading && resources.length === 0) {
    return (
      <Segment placeholder style={{ minHeight: "300px" }}>
        <Loader active size="large">
          Loading content types...
        </Loader>
      </Segment>
    );
  }

  if (error) {
    return (
      <Message negative icon>
        <Icon name="warning circle" />
        <Message.Content>
          <Message.Header>Error loading resources</Message.Header>
          <p>{error}</p>
        </Message.Content>
      </Message>
    );
  }

  // Group resources by category
  const singletons = resources.filter((r) => r.is_singleton);
  const collections = resources.filter((r) => !r.is_singleton);

  const renderResourceCard = (resource) => (
    <Card
      key={resource.type}
      onClick={() => onSelectResource(resource.type, resource)}
      style={{ cursor: "pointer" }}
      raised
    >
      <Card.Content>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            marginBottom: "0.75rem",
          }}
        >
          <Icon
            name={getResourceIcon(resource.type)}
            size="big"
            color={getResourceColor(resource.type)}
            style={{ marginRight: "0.75rem" }}
          />
          <div style={{ flex: 1 }}>
            <Card.Header style={{ marginBottom: "0.25rem" }}>
              {resource.label}
            </Card.Header>
            <Label
              size="tiny"
              color={resource.output_format === "html" ? "blue" : "green"}
              style={{ marginRight: "0.5rem" }}
            >
              {resource.output_format.toUpperCase()}
            </Label>
          </div>
        </div>
        <Card.Description style={{ color: "#666", fontSize: "0.9rem" }}>
          {resource.description}
        </Card.Description>
      </Card.Content>
      <Card.Content extra>
        <Button
          primary
          fluid
          size="small"
          icon="arrow right"
          labelPosition="right"
          content="Manage"
        />
      </Card.Content>
    </Card>
  );

  return (
    <div className="resource-list">
      {/* Singleton Resources */}
      {singletons.length > 0 && (
        <div style={{ marginBottom: "2rem" }}>
          <Header as="h3" dividing style={{ color: "#555" }}>
            <Icon name="cube" />
            <Header.Content>
              Site Components
              <Header.Subheader>
                Single-instance content blocks (one per language)
              </Header.Subheader>
            </Header.Content>
          </Header>
          <Card.Group itemsPerRow={3} stackable>
            {singletons.map(renderResourceCard)}
          </Card.Group>
        </div>
      )}

      {/* Collection Resources */}
      {collections.length > 0 && (
        <div>
          <Header as="h3" dividing style={{ color: "#555" }}>
            <Icon name="copy outline" />
            <Header.Content>
              Content Collections
              <Header.Subheader>
                Multiple content items per type
              </Header.Subheader>
            </Header.Content>
          </Header>
          <Card.Group itemsPerRow={3} stackable>
            {collections.map(renderResourceCard)}
          </Card.Group>
        </div>
      )}

      {resources.length === 0 && !loading && (
        <Message info icon>
          <Icon name="info circle" />
          <Message.Content>
            <Message.Header>No resource types available</Message.Header>
            <p>
              Resource types are configured in the backend. Contact an
              administrator if you need to add new content types.
            </p>
          </Message.Content>
        </Message>
      )}
    </div>
  );
};

ResourceList.propTypes = {
  onSelectResource: PropTypes.func.isRequired,
};

export default ResourceList;
