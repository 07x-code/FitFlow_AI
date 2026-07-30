import { Navigate, Route, Routes } from 'react-router';

import { AppShell } from './components/app-shell';
import { CoachPage } from './pages/coach-page';
import { DashboardPage } from './pages/dashboard-page';
import { ExercisePage } from './pages/exercise-page';
import { LoginPage } from './pages/login-page';
import { PlanDetailPage } from './pages/plan-detail-page';
import { PlansPage } from './pages/plans-page';
import { ProfilePage } from './pages/profile-page';
import { ProfileSetupPage } from './pages/profile-setup-page';
import { ProgressPage } from './pages/progress-page';
import { WorkoutPage } from './pages/workout-page';

export function App() {
  return (
    <Routes>
      <Route element={<LoginPage />} path="/" />
      <Route element={<ProfileSetupPage />} path="/profile-setup" />
      <Route element={<AppShell />} path="/app">
        <Route element={<DashboardPage />} index />
        <Route element={<PlansPage />} path="plans" />
        <Route element={<PlanDetailPage />} path="plans/:planId" />
        <Route element={<WorkoutPage />} path="workouts/:workoutId" />
        <Route element={<ExercisePage />} path="exercises/:exerciseId" />
        <Route element={<CoachPage />} path="coach" />
        <Route element={<ProgressPage />} path="progress" />
        <Route element={<ProfilePage />} path="profile" />
      </Route>
      <Route element={<Navigate replace to="/" />} path="*" />
    </Routes>
  );
}

