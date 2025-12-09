// Confirmation Modal Component
// Reusable modal for delete confirmations

import React from "react";
import { Modal, Button, Icon } from "semantic-ui-react";
import PropTypes from "prop-types";

const ConfirmModal = ({
  open,
  onClose,
  onConfirm,
  title = "Confirm Action",
  message = "Are you sure you want to proceed?",
  confirmText = "Confirm",
  cancelText = "Cancel",
  confirmColor = "red",
  loading = false,
}) => {
  return (
    <Modal
      size="small"
      open={open}
      onClose={onClose}
      closeOnDimmerClick={!loading}
    >
      <Modal.Header>
        <Icon name="warning sign" color="orange" />
        {title}
      </Modal.Header>
      <Modal.Content>
        <p>{message}</p>
      </Modal.Content>
      <Modal.Actions>
        <Button basic onClick={onClose} disabled={loading}>
          {cancelText}
        </Button>
        <Button
          color={confirmColor}
          onClick={onConfirm}
          loading={loading}
          disabled={loading}
        >
          <Icon name="checkmark" />
          {confirmText}
        </Button>
      </Modal.Actions>
    </Modal>
  );
};

ConfirmModal.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onConfirm: PropTypes.func.isRequired,
  title: PropTypes.string,
  message: PropTypes.string,
  confirmText: PropTypes.string,
  cancelText: PropTypes.string,
  confirmColor: PropTypes.string,
  loading: PropTypes.bool,
};

export default ConfirmModal;
