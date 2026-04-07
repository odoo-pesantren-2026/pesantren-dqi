// async fetchAndProcessData(startDate, endDate) {
//     this.showLoading();
//     try {
//       let leadSourceData = [];
//       let winLossData = [];
//       let industryData = [];
//       const domain = [];

//       // Set default dates if not provided
//       if (!startDate) {
//         const today = new Date();
//         const firstDayOfMonth = new Date(
//           Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 1, 0, 0, 1)
//         );
//         startDate = firstDayOfMonth.toISOString().split("T")[0];
//       }

//       if (!endDate) {
//         const today = new Date();
//         const lastDayOfMonth = new Date(
//           Date.UTC(
//             today.getUTCFullYear(),
//             today.getUTCMonth(),
//             today.getUTCDate(),
//             23,
//             59,
//             59,
//             999
//           )
//         );
//         endDate = lastDayOfMonth.toISOString().split("T")[0];
//       }

//       // Add date range to domain
//       domain.push(["create_date", ">=", startDate]);
//       domain.push(["create_date", "<=", endDate]);

//       if (this.props.title === "leadSources") {
//         // Fetch lead sources data
//         leadSourceData = await this.orm.call("crm.lead", "search_read", [
//           domain,
//           ["id", "lead_source"],
//         ]);
//       } else if (this.props.title === "winLossRatio") {
//         // Fetch win/loss data
//         winLossData = await this.orm.call("crm.lead", "search_read", [
//           domain,
//           ["id", "probability", "stage_id"],
//         ]);
//       } else if (this.props.title === "industryBreakdown") {
//         // Fetch industry breakdown data
//         industryData = await this.orm.call("crm.lead", "search_read", [
//           domain,
//           ["id", "industry"],
//         ]);
//       }

//       await this.processData(leadSourceData, winLossData, industryData);
//     } catch (error) {
//       console.error("Error fetching data from Odoo:", error);
//     } finally {
//       this.hideLoading();
//     }
//   }

//   async processData(leadSourceData, winLossData, industryData) {
//     const aggregateData = (data, key) => {
//       const stateCounts = {};
//       data.forEach((record) => {
//         const value = record[key] || "Unknown";
//         if (!stateCounts[value]) {
//           stateCounts[value] = { count: 0, ids: [] };
//         }
//         stateCounts[value].count += 1;
//         stateCounts[value].ids.push(record.id);
//       });
//       return stateCounts;
//     };

//     if (this.props.title === "leadSources") {
//       const sourceCounts = aggregateData(leadSourceData, "lead_source");

//       // Map lead sources to more readable labels
//       const sourceMappers = {
//         "website": "Website",
//         "email": "Email",
//         "phone": "Telepon",
//         "event": "Event",
//         "referral": "Referral"
//       };

//       this.state.originalLabels = Object.keys(sourceCounts).map(source =>
//         sourceMappers[source.toLowerCase()] || source
//       );

//       this.state.labels = this.state.originalLabels;

//       this.state.datasets = [{
//         label: "Sumber Lead",
//         data: Object.values(sourceCounts).map(item => item.count),
//         backgroundColor: this.state.labels.map((_, index) =>
//           this.getDiverseGradientColor(index, this.state.labels.length)
//         ),
//         borderColor: "#ffffff",
//         borderWidth: 1,
//         hoverOffset: 4,
//         associated_ids: Object.values(sourceCounts).map(item => item.ids),
//       }];

//     } else if (this.props.title === "winLossRatio") {
//       const winCount = winLossData.filter(lead =>
//         lead.probability >= 80 || (lead.stage_id && lead.stage_id[1] === "Won")
//       ).length;
//       const lossCount = winLossData.length - winCount;

//       this.state.labels = ["Menang", "Kalah"];
//       this.state.datasets = [{
//         label: "Win/Loss Ratio",
//         data: [winCount, lossCount],
//         backgroundColor: [
//           "rgba(75, 192, 192, 0.6)",  // Green for wins
//           "rgba(255, 99, 132, 0.6)"   // Red for losses
//         ],
//         borderColor: "#ffffff",
//         borderWidth: 1,
//         hoverOffset: 4,
//       }];

//     } else if (this.props.title === "industryBreakdown") {
//       const industryCounts = aggregateData(industryData, "industry");

//       // Predefined industry labels
//       const industryMappers = {
//         "retail": "Retail",
//         "it": "IT",
//         "finance": "Keuangan",
//         "manufacturing": "Manufaktur",
//         "technology": "Teknologi"
//       };

//       this.state.originalLabels = Object.keys(industryCounts).map(industry =>
//         industryMappers[industry.toLowerCase()] || industry
//       );

//       this.state.labels = this.state.originalLabels;

//       this.state.datasets = [{
//         label: "Industri Lead",
//         data: Object.values(industryCounts).map(item => item.count),
//         backgroundColor: this.state.labels.map((_, index) =>
//           this.getDiverseGradientColor(index, this.state.labels.length)
//         ),
//         borderColor: "#ffffff",
//         borderWidth: 1,
//         hoverOffset: 4,
//         associated_ids: Object.values(industryCounts).map(item => item.ids),
//       }];
//     }

//     this.renderChart();
//   }
