import { createRouter, createWebHistory } from "vue-router";

import DashboardView from "../views/DashboardView.vue";
import NodesView from "../views/NodesView.vue";
import RelationshipsView from "../views/RelationshipsView.vue";
import CSVUploadView from "../views/CSVUploadView.vue";
import FraudQueriesView from "../views/FraudQueriesView.vue";
import GDSView from "../views/GDSView.vue";
import GraphView from "../views/GraphView.vue";

const routes = [
  { path: "/", name: "dashboard", component: DashboardView },
  { path: "/nodes", name: "nodes", component: NodesView },
  { path: "/relationships", name: "relationships", component: RelationshipsView },
  { path: "/csv", name: "csv", component: CSVUploadView },
  { path: "/fraud", name: "fraud", component: FraudQueriesView },
  { path: "/gds", name: "gds", component: GDSView },
  { path: "/graph", name: "graph", component: GraphView }
];

export default createRouter({
  history: createWebHistory(),
  routes
});
