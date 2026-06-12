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
  Modal,
} from "semantic-ui-react";
import { useResourceCMSApi } from "../../hooks";

/**
 * ResourceList - Shows all available CMS resource types as cards
 */
export const ResourceList = ({ onSelectResource }) => {
  const { listResources, loading, error } = useResourceCMSApi();
  const [resources, setResources] = useState([]);
  const [reindexing, setReindexing] = useState(false);
  const [reindexMessage, setReindexMessage] = useState(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [reindexStatus, setReindexStatus] = useState(null);

  // Patch Regions state
  const [patching, setPatching] = useState(false);
  const [patchMessage, setPatchMessage] = useState(null);
  const [patchConfirmOpen, setPatchConfirmOpen] = useState(false);
  const [patchStatus, setPatchStatus] = useState(null);

  // Migrate Resource Types state
  const [migratingTypes, setMigratingTypes] = useState(false);
  const [migrateTypesMessage, setMigrateTypesMessage] = useState(null);
  const [migrateTypesConfirmOpen, setMigrateTypesConfirmOpen] = useState(false);
  const [migrateTypesStatus, setMigrateTypesStatus] = useState(null);

  // Poll reindex status
  useEffect(() => {
    if (!reindexing) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch("/data/reindex", {
          headers: { "Content-Type": "application/json" },
        });
        const data = await res.json();
        setReindexStatus(data);

        if (data.status === "completed") {
          setReindexing(false);
          setReindexMessage({ type: "success", text: data.message });
        } else if (data.status === "failed") {
          setReindexing(false);
          setReindexMessage({ type: "error", text: data.message });
        }
      } catch (_) {
        // ignore polling errors
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [reindexing]);

  // Trigger reindex
  const handleReindex = async () => {
    setConfirmOpen(false);
    setReindexing(true);
    setReindexMessage(null);
    setReindexStatus(null);
    try {
      const response = await fetch("/data/reindex", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      const data = await response.json();
      if (response.ok) {
        setReindexMessage({ type: "info", text: data.message });
      } else if (response.status === 409) {
        setReindexMessage({ type: "info", text: data.message });
      } else {
        setReindexing(false);
        setReindexMessage({
          type: "error",
          text: data.error || "Failed to trigger reindex",
        });
      }
    } catch (err) {
      setReindexing(false);
      setReindexMessage({ type: "error", text: err.message });
    }
  };

  // Poll patch regions status
  useEffect(() => {
    if (!patching) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch("/data/patch-regions", {
          headers: { "Content-Type": "application/json" },
        });
        const data = await res.json();
        setPatchStatus(data);

        if (data.status === "completed") {
          setPatching(false);
          setPatchMessage({ type: "success", text: data.message });
        } else if (data.status === "failed") {
          setPatching(false);
          setPatchMessage({ type: "error", text: data.message });
        }
      } catch (_) {
        // ignore polling errors
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [patching]);

  // Trigger patch regions
  const handlePatchRegions = async () => {
    setPatchConfirmOpen(false);
    setPatching(true);
    setPatchMessage(null);
    setPatchStatus(null);
    try {
      const response = await fetch("/data/patch-regions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      const data = await response.json();
      if (response.ok) {
        setPatchMessage({ type: "info", text: data.message });
      } else if (response.status === 409) {
        setPatchMessage({ type: "info", text: data.message });
      } else {
        setPatching(false);
        setPatchMessage({
          type: "error",
          text: data.error || "Failed to trigger patch",
        });
      }
    } catch (err) {
      setPatching(false);
      setPatchMessage({ type: "error", text: err.message });
    }
  };

  // Poll migrate resource types status
  useEffect(() => {
    if (!migratingTypes) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch("/data/patch-resource-types", {
          headers: { "Content-Type": "application/json" },
        });
        const data = await res.json();
        setMigrateTypesStatus(data);

        if (data.status === "completed") {
          setMigratingTypes(false);
          setMigrateTypesMessage({ type: "success", text: data.message });
        } else if (data.status === "failed") {
          setMigratingTypes(false);
          setMigrateTypesMessage({ type: "error", text: data.message });
        }
      } catch (_) {
        // ignore polling errors
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [migratingTypes]);

  // Trigger migrate resource types
  const handleMigrateTypes = async () => {
    setMigrateTypesConfirmOpen(false);
    setMigratingTypes(true);
    setMigrateTypesMessage(null);
    setMigrateTypesStatus(null);
    try {
      const response = await fetch("/data/patch-resource-types", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      const data = await response.json();
      if (response.ok) {
        setMigrateTypesMessage({ type: "info", text: data.message });
      } else if (response.status === 409) {
        setMigrateTypesMessage({ type: "info", text: data.message });
      } else {
        setMigratingTypes(false);
        setMigrateTypesMessage({
          type: "error",
          text: data.error || "Failed to trigger migration",
        });
      }
    } catch (err) {
      setMigratingTypes(false);
      setMigrateTypesMessage({ type: "error", text: err.message });
    }
  };

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
      header_frontpage: "home",
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
      className="cms-resource-card"
      raised
    >
      <Card.Content>
        <div className="cms-resource-card-header">
          <Icon
            name={getResourceIcon(resource.type)}
            size="big"
            className="cms-resource-card-icon"
          />
          <div style={{ flex: 1 }}>
            <Card.Header className="cms-resource-card-title">
              {resource.label}
            </Card.Header>
            <Label size="tiny" className="cms-resource-card-format">
              {resource.output_format.toUpperCase()}
            </Label>
          </div>
        </div>
        <Card.Description className="cms-resource-card-description">
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
          className="cms-btn-primary"
        />
      </Card.Content>
    </Card>
  );

  return (
    <div className="resource-list cms-resource-list">
      {/* Singleton Resources */}
      {singletons.length > 0 && (
        <div className="cms-resource-section">
          <Header as="h3" dividing className="cms-section-header">
            <Icon name="cube" className="cms-section-icon" />
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
        <div className="cms-resource-section">
          <Header as="h3" dividing className="cms-section-header">
            <Icon name="copy outline" className="cms-section-icon" />
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

      {/* Administration Actions */}
      <div className="cms-resource-section">
        <Header as="h3" dividing className="cms-section-header">
          <Icon name="cogs" className="cms-section-icon" />
          <Header.Content>
            Administration
            <Header.Subheader>System maintenance actions</Header.Subheader>
          </Header.Content>
        </Header>

        {reindexMessage && (
          <Message
            positive={reindexMessage.type === "success"}
            negative={reindexMessage.type === "error"}
            info={reindexMessage.type === "info"}
            onDismiss={() => setReindexMessage(null)}
            icon
          >
            <Icon name={reindexMessage.type === "success" ? "check circle" : reindexMessage.type === "error" ? "times circle" : "info circle"} />
            <Message.Content>
              <Message.Header>
                {reindexMessage.type === "success" ? "Success" : reindexMessage.type === "error" ? "Error" : "In Progress"}
              </Message.Header>
              {reindexMessage.text}
              {reindexing && reindexStatus?.started_at && (
                <span style={{ marginLeft: "1em", opacity: 0.7 }}>
                  (Started: {new Date(reindexStatus.started_at).toLocaleTimeString()})
                </span>
              )}
            </Message.Content>
          </Message>
        )}

        <Segment>
          <Grid verticalAlign="middle">
            <Grid.Column width={12}>
              <Header as="h4">
                <Icon name="sync alternate" />
                <Header.Content>
                  Rebuild Search Index
                  <Header.Subheader>
                    Rebuild OpenSearch indices for all records. Use this if
                    search results appear out of sync with the database. The
                    process runs in the background and may take several minutes.
                  </Header.Subheader>
                </Header.Content>
              </Header>
            </Grid.Column>
            <Grid.Column width={4} textAlign="right">
              <Button
                color="orange"
                icon
                labelPosition="left"
                loading={reindexing}
                disabled={reindexing}
                onClick={() => setConfirmOpen(true)}
              >
                <Icon name="sync alternate" />
                {reindexing ? "Reindexing..." : "Rebuild Index"}
              </Button>
            </Grid.Column>
          </Grid>
        </Segment>

        {/* Confirmation Modal */}
        <Modal
          size="small"
          open={confirmOpen}
          onClose={() => setConfirmOpen(false)}
        >
          <Modal.Header>
            <Icon name="warning sign" color="orange" /> Confirm Rebuild Index
          </Modal.Header>
          <Modal.Content>
            <p>
              This will rebuild the entire OpenSearch index. The process runs in
              the background and may take several minutes to complete.
            </p>
            <p>Search results may be temporarily incomplete during reindexing.</p>
          </Modal.Content>
          <Modal.Actions>
            <Button onClick={() => setConfirmOpen(false)}>Cancel</Button>
            <Button color="orange" onClick={handleReindex}>
              <Icon name="sync alternate" /> Rebuild Index
            </Button>
          </Modal.Actions>
        </Modal>

        {/* Patch Affiliation Regions */}
        {patchMessage && (
          <Message
            positive={patchMessage.type === "success"}
            negative={patchMessage.type === "error"}
            info={patchMessage.type === "info"}
            onDismiss={() => setPatchMessage(null)}
            icon
          >
            <Icon name={patchMessage.type === "success" ? "check circle" : patchMessage.type === "error" ? "times circle" : "info circle"} />
            <Message.Content>
              <Message.Header>
                {patchMessage.type === "success" ? "Success" : patchMessage.type === "error" ? "Error" : "In Progress"}
              </Message.Header>
              {patchMessage.text}
              {patching && patchStatus?.started_at && (
                <span style={{ marginLeft: "1em", opacity: 0.7 }}>
                  (Started: {new Date(patchStatus.started_at).toLocaleTimeString()})
                </span>
              )}
            </Message.Content>
          </Message>
        )}

        <Segment>
          <Grid verticalAlign="middle">
            <Grid.Column width={12}>
              <Header as="h4">
                <Icon name="globe" />
                <Header.Content>
                  Patch Affiliation Regions
                  <Header.Subheader>
                    Populate affiliation regions on existing records by deriving
                    UNESCO regional groups from country data. Records that
                    already have regions set will be skipped.
                  </Header.Subheader>
                </Header.Content>
              </Header>
            </Grid.Column>
            <Grid.Column width={4} textAlign="right">
              <Button
                color="teal"
                icon
                labelPosition="left"
                loading={patching}
                disabled={patching}
                onClick={() => setPatchConfirmOpen(true)}
              >
                <Icon name="play" />
                {patching ? "Patching..." : "Patch Regions"}
              </Button>
            </Grid.Column>
          </Grid>
        </Segment>

        {/* Patch Regions Confirmation Modal */}
        <Modal
          size="small"
          open={patchConfirmOpen}
          onClose={() => setPatchConfirmOpen(false)}
        >
          <Modal.Header>
            <Icon name="globe" color="teal" /> Confirm Patch Affiliation Regions
          </Modal.Header>
          <Modal.Content>
            <p>
              This will update existing records to populate affiliation
              regions derived from country data. The process runs in the
              background and may take several minutes.
            </p>
            <p>Records that already have regions set will be skipped.</p>
          </Modal.Content>
          <Modal.Actions>
            <Button onClick={() => setPatchConfirmOpen(false)}>Cancel</Button>
            <Button color="teal" onClick={handlePatchRegions}>
              <Icon name="play" /> Patch Regions
            </Button>
          </Modal.Actions>
        </Modal>

        {/* Migrate Resource Types */}
        {migrateTypesMessage && (
          <Message
            positive={migrateTypesMessage.type === "success"}
            negative={migrateTypesMessage.type === "error"}
            info={migrateTypesMessage.type === "info"}
            onDismiss={() => setMigrateTypesMessage(null)}
            icon
          >
            <Icon name={migrateTypesMessage.type === "success" ? "check circle" : migrateTypesMessage.type === "error" ? "times circle" : "info circle"} />
            <Message.Content>
              <Message.Header>
                {migrateTypesMessage.type === "success" ? "Success" : migrateTypesMessage.type === "error" ? "Error" : "In Progress"}
              </Message.Header>
              {migrateTypesMessage.text}
              {migratingTypes && migrateTypesStatus?.started_at && (
                <span style={{ marginLeft: "1em", opacity: 0.7 }}>
                  (Started: {new Date(migrateTypesStatus.started_at).toLocaleTimeString()})
                </span>
              )}
            </Message.Content>
          </Message>
        )}

        <Segment>
          <Grid verticalAlign="middle">
            <Grid.Column width={12}>
              <Header as="h4">
                <Icon name="tags" />
                <Header.Content>
                  Migrate Resource Types
                  <Header.Subheader>
                    Consolidate standalone resource types (dataset, software,
                    other) into "publication-other" on existing records, so the
                    resource-type facet shows a single "Other" entry. Records
                    already using a publication type are skipped.
                  </Header.Subheader>
                </Header.Content>
              </Header>
            </Grid.Column>
            <Grid.Column width={4} textAlign="right">
              <Button
                color="purple"
                icon
                labelPosition="left"
                loading={migratingTypes}
                disabled={migratingTypes}
                onClick={() => setMigrateTypesConfirmOpen(true)}
              >
                <Icon name="tags" />
                {migratingTypes ? "Migrating..." : "Migrate Types"}
              </Button>
            </Grid.Column>
          </Grid>
        </Segment>

        {/* Migrate Resource Types Confirmation Modal */}
        <Modal
          size="small"
          open={migrateTypesConfirmOpen}
          onClose={() => setMigrateTypesConfirmOpen(false)}
        >
          <Modal.Header>
            <Icon name="tags" color="purple" /> Confirm Migrate Resource Types
          </Modal.Header>
          <Modal.Content>
            <p>
              This will update existing records whose resource type is
              "dataset", "software" or "other" to "publication-other". The
              process runs in the background and may take several minutes.
            </p>
            <p>Records already using a publication type will be skipped.</p>
          </Modal.Content>
          <Modal.Actions>
            <Button onClick={() => setMigrateTypesConfirmOpen(false)}>Cancel</Button>
            <Button color="purple" onClick={handleMigrateTypes}>
              <Icon name="tags" /> Migrate Types
            </Button>
          </Modal.Actions>
        </Modal>
      </div>
    </div>
  );
};

ResourceList.propTypes = {
  onSelectResource: PropTypes.func.isRequired,
};

export default ResourceList;
