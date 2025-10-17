/**
 * UNESCO Science Portal Statistics Dashboard
 *
 * This module handles the statistics dashboard functionality including:
 * - Fetching data from the statistics API endpoint
 * - Rendering charts and data visualizations
 * - Handling user interactions and data refresh
 */

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
   * Render activity chart using Canvas
   */
  renderActivityChart(dailyActivity) {
    const canvas = document.getElementById("activity-canvas");
    const ctx = canvas.getContext("2d");

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Set up chart parameters
    const padding = 40;
    const chartWidth = canvas.width - 2 * padding;
    const chartHeight = canvas.height - 2 * padding;

    // Extract data
    const uploads = dailyActivity.map((d) => d.uploads);
    const downloads = dailyActivity.map((d) => d.downloads);
    const dates = dailyActivity.map((d) => d.date);

    // Find max values for scaling
    const maxUploads = Math.max(...uploads);
    const maxDownloads = Math.max(...downloads);
    const maxValue = Math.max(maxUploads, maxDownloads);

    // Draw axes
    ctx.strokeStyle = "#ddd";
    ctx.lineWidth = 1;

    // Y axis
    ctx.beginPath();
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, canvas.height - padding);
    ctx.stroke();

    // X axis
    ctx.beginPath();
    ctx.moveTo(padding, canvas.height - padding);
    ctx.lineTo(canvas.width - padding, canvas.height - padding);
    ctx.stroke();

    // Draw upload line (blue)
    this.drawLine(
      ctx,
      canvas,
      uploads,
      maxValue,
      chartWidth,
      chartHeight,
      padding,
      "#2185d0",
      "Uploads"
    );

    // Draw download line (green)
    this.drawLine(
      ctx,
      canvas,
      downloads,
      maxValue,
      chartWidth,
      chartHeight,
      padding,
      "#21ba45",
      "Downloads"
    );

    // Add legend
    this.drawLegend(ctx, canvas);
  }

  /**
   * Draw a line on the chart
   */
  drawLine(
    ctx,
    canvas,
    data,
    maxValue,
    chartWidth,
    chartHeight,
    padding,
    color,
    label
  ) {
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.beginPath();

    data.forEach((value, index) => {
      const x = padding + (index / (data.length - 1)) * chartWidth;
      const y = canvas.height - padding - (value / maxValue) * chartHeight;

      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });

    ctx.stroke();

    // Draw points
    ctx.fillStyle = color;
    data.forEach((value, index) => {
      const x = padding + (index / (data.length - 1)) * chartWidth;
      const y = canvas.height - padding - (value / maxValue) * chartHeight;

      ctx.beginPath();
      ctx.arc(x, y, 3, 0, 2 * Math.PI);
      ctx.fill();
    });
  }

  /**
   * Draw chart legend
   */
  drawLegend(ctx, canvas) {
    const legendY = 20;

    // Uploads legend
    ctx.fillStyle = "#2185d0";
    ctx.fillRect(canvas.width - 150, legendY, 10, 10);
    ctx.fillStyle = "#333";
    ctx.font = "12px Arial";
    ctx.fillText("Uploads", canvas.width - 135, legendY + 8);

    // Downloads legend
    ctx.fillStyle = "#21ba45";
    ctx.fillRect(canvas.width - 150, legendY + 20, 10, 10);
    ctx.fillStyle = "#333";
    ctx.fillText("Downloads", canvas.width - 135, legendY + 28);
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
      item.className = "event";

      // Choose icon based on action
      let icon = "file";
      if (activity.action.includes("uploaded")) icon = "upload";
      else if (activity.action.includes("downloaded")) icon = "download";
      else if (activity.action.includes("created")) icon = "plus";
      else if (activity.action.includes("published")) icon = "globe";

      item.innerHTML = `
                <div class="label">
                    <i class="${icon} icon"></i>
                </div>
                <div class="content">
                    <div class="summary">
                        <strong>${activity.action}</strong>: ${activity.title}
                        <div class="date">${activity.time}</div>
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
