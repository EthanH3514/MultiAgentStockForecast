import { createRouter, createWebHistory } from 'vue-router';
import StockPrediction from '../views/StockPrediction.vue';
import Settings from '../views/Settings.vue';

const routes = [
  {
    path: '/',
    name: 'home',
    component: StockPrediction,
  },
  {
    path: '/settings',
    name: 'settings',
    component: Settings,
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

export default router;