// CMS Navigation Component
// Tab navigation for switching between Pages and Categories views

import React from "react";
import { Menu, Icon } from "semantic-ui-react";
import PropTypes from "prop-types";

const CMSNavigation = ({ activeView, onViewChange }) => {
  return (
    <Menu pointing secondary className="cms-navigation">
      <Menu.Item
        name="pages"
        active={activeView === "pages"}
        onClick={() => onViewChange("pages")}
      >
        <Icon name="file alternate outline" />
        Pages
      </Menu.Item>
      <Menu.Item
        name="categories"
        active={activeView === "categories"}
        onClick={() => onViewChange("categories")}
      >
        <Icon name="tags" />
        Categories
      </Menu.Item>
    </Menu>
  );
};

CMSNavigation.propTypes = {
  activeView: PropTypes.oneOf(["pages", "categories"]).isRequired,
  onViewChange: PropTypes.func.isRequired,
};

export default CMSNavigation;
