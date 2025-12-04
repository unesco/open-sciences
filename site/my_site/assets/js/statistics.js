/**
 * UNESCO Science Portal Statistics Dashboard
 *
 * This module handles the statistics dashboard functionality including:
 * - Fetching data from the statistics API endpoint
 * - Rendering charts and data visualizations
 * - Handling user interactions and data refresh
 */

/* global Chart */

class StatisticsDashboard {
  constructor() {
    this.apiEndpoint = "/data/statistics";
    this.chart = null;
    this.init();
  }

  /**
   * Initialize the dashboard
   */
  init() {
    // Load statistics when the page is ready
    document.addEventListener("DOMContentLoaded", () => {
      this.loadData();
    });

    // Make refreshStatistics globally available
    window.refreshStatistics = () => this.loadData();
  }

  /**
   * Load statistics data from the API
   */
  /**
   * Load statistics data from the API
   */
  async loadData() {
    try {
      console.log("Loading statistics data...");
      this.showLoading();

      const response = await fetch("/data/statistics");
      console.log("Response status:", response.status);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("Data loaded successfully:", data);
      this.renderDashboard(data);
    } catch (error) {
      console.error("Error loading statistics:", error);
      this.showError("Failed to load statistics data: " + error.message);
    } finally {
      this.hideLoading();
    }
  }

  /**
   * Hide loading state
   */
  hideLoading() {
    document.getElementById("loading-stats").style.display = "none";
  }
  /**
   * Show loading state
   */
  showLoading() {
    document.getElementById("loading-stats").style.display = "block";
    document.getElementById("statistics-dashboard").style.display = "none";
    document.getElementById("error-state").style.display = "none";
  }

  /**
   * Show error state
   */
  showError(message) {
    console.error("Statistics Dashboard Error:", message);
    document.getElementById("loading-stats").style.display = "none";
    document.getElementById("statistics-dashboard").style.display = "none";
    document.getElementById("error-state").style.display = "block";

    // Display error message if there's an error container
    const errorMessage = document.getElementById("error-message");
    if (errorMessage) {
      errorMessage.textContent = message;
    }
  }

  /**
   * Render the complete dashboard with data
   */
  renderDashboard(data) {
    // Hide loading, show dashboard
    document.getElementById("loading-stats").style.display = "none";
    document.getElementById("error-state").style.display = "none";
    document.getElementById("statistics-dashboard").style.display = "block";

    // Render summary statistics
    this.renderSummary(data.summary);

    // Render activity chart
    this.renderActivityChart(data.daily_activity);

    // Render top subjects
    this.renderTopSubjects(data.top_subjects);

    // Render recent activities
    this.renderRecentActivities(data.recent_activities);

    // Update last updated time
    document.getElementById("last-updated").textContent = data.last_updated;
  }

  /**
   * Render summary statistics cards
   */
  renderSummary(summary) {
    document.getElementById("total-records").textContent = this.formatNumber(
      summary.total_records
    );
    document.getElementById("total-downloads").textContent = this.formatNumber(
      summary.total_downloads
    );
    document.getElementById("active-users").textContent = this.formatNumber(
      summary.active_users
    );
    document.getElementById(
      "growth-rate"
    ).innerHTML = `${summary.growth_rate}<span style="font-size: 0.6em;">%</span>`;
  }

  /**
   * Render activity chart using Chart.js
   */
  renderActivityChart(dailyActivity) {
    const canvas = document.getElementById("activity-canvas");
    const ctx = canvas.getContext("2d");

    // Destroy existing chart if it exists
    if (this.chart) {
      this.chart.destroy();
    }

    // Extract data
    const labels = dailyActivity.map((d) => {
      const date = new Date(d.date);
      return date.toLocaleDateString("it-IT", {
        month: "short",
        day: "numeric",
      });
    });
    const uploads = dailyActivity.map((d) => d.uploads);
    const downloads = dailyActivity.map((d) => d.downloads);

    // Create Chart.js chart with UNESCO colors
    this.chart = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Uploads",
            data: uploads,
            borderColor: "#0077C8",
            backgroundColor: "rgba(0, 119, 200, 0.1)",
            tension: 0.4,
            fill: true,
            pointRadius: 4,
            pointHoverRadius: 6,
            pointBackgroundColor: "#0077C8",
            pointBorderColor: "#fff",
            pointBorderWidth: 2,
          },
          {
            label: "Downloads",
            data: downloads,
            borderColor: "#00B398",
            backgroundColor: "rgba(0, 179, 152, 0.1)",
            tension: 0.4,
            fill: true,
            pointRadius: 4,
            pointHoverRadius: 6,
            pointBackgroundColor: "#00B398",
            pointBorderColor: "#fff",
            pointBorderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: "index",
          intersect: false,
        },
        plugins: {
          legend: {
            display: true,
            position: "top",
            labels: {
              usePointStyle: true,
              padding: 15,
              font: {
                size: 13,
                weight: "500",
              },
            },
          },
          tooltip: {
            backgroundColor: "rgba(0, 0, 0, 0.8)",
            padding: 12,
            titleFont: {
              size: 14,
              weight: "600",
            },
            bodyFont: {
              size: 13,
            },
            borderColor: "rgba(255, 255, 255, 0.1)",
            borderWidth: 1,
            displayColors: true,
            callbacks: {
              label: function (context) {
                return (
                  context.dataset.label +
                  ": " +
                  context.parsed.y.toLocaleString()
                );
              },
            },
          },
        },
        scales: {
          x: {
            grid: {
              display: false,
            },
            ticks: {
              maxRotation: 45,
              minRotation: 0,
              font: {
                size: 11,
              },
            },
          },
          y: {
            beginAtZero: true,
            grid: {
              color: "rgba(0, 0, 0, 0.05)",
            },
            ticks: {
              font: {
                size: 11,
              },
              callback: function (value) {
                return value.toLocaleString();
              },
            },
          },
        },
      },
    });
  }

  /**
   * Render top subjects list
   */
  renderTopSubjects(topSubjects) {
    const container = document.getElementById("top-subjects");
    container.innerHTML = "";

    topSubjects.forEach((subject, index) => {
      const item = document.createElement("div");
      item.className = "item";

      const percentage = Math.round(
        (subject.count / topSubjects[0].count) * 100
      );

      item.innerHTML = `
                <div class="content">
                    <div class="header">${subject.name}</div>
                    <div class="description">
                        ${this.formatNumber(subject.count)} records
                        <div class="ui tiny progress" style="margin-top: 5px;">
                            <div class="bar" style="width: ${percentage}%; background-color: hsl(${
        200 + index * 30
      }, 60%, 50%);"></div>
                        </div>
                    </div>
                </div>
            `;

      container.appendChild(item);
    });
  }

  /**
   * Render recent activities feed
   */
  renderRecentActivities(activities) {
    const container = document.getElementById("recent-activities");
    container.innerHTML = "";

    activities.forEach((activity) => {
      const item = document.createElement("div");
      item.className = "activity-item";

      // Choose emoji based on action
      let emoji = "📄";
      if (activity.action.includes("uploaded")) emoji = "⬆️";
      else if (activity.action.includes("downloaded")) emoji = "⬇️";
      else if (activity.action.includes("created")) emoji = "✨";
      else if (activity.action.includes("published")) emoji = "🌍";

      item.innerHTML = `
        <div style="display: flex; gap: 12px; align-items: start;">
          <div style="font-size: 20px; flex-shrink: 0;">${emoji}</div>
          <div style="flex: 1;">
            <div class="activity-action">${activity.action}</div>
            <div style="color: rgba(0, 0, 0, 0.65); margin-top: 4px;">${activity.title}</div>
            <div class="activity-time">${activity.time}</div>
          </div>
        </div>
      `;

      container.appendChild(item);
    });
  }

  /**
   * Format numbers with commas
   */
  formatNumber(num) {
    return num.toLocaleString();
  }
}

// Initialize the dashboard
const dashboard = new StatisticsDashboard();
