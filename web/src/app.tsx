import { Navigate, Route, Routes } from 'react-router';

import { AppShell } from './components/app-shell';
import { RequireAuth } from './auth';
import { CoachPage } from './pages/coach-page';
import { DashboardPage } from './pages/dashboard-page';
import { ExercisePage } from './pages/exercise-page';
import { ExerciseLibraryPage } from './pages/exercise-library-page';
import { LoginPage } from './pages/login-page';
import { RegisterPage } from './pages/register-page';
import { PlanDetailPage } from './pages/plan-detail-page';
import { PlansPage } from './pages/plans-page';
import { ProfilePage } from './pages/profile-page';
import { ProfileSetupPage } from './pages/profile-setup-page';
import { WorkoutPage } from './pages/workout-page';

export function App() {
  return (
    <Routes>
      <Route element={<LoginPage />} path="/" />
      <Route element={<RegisterPage />} path="/register" />
      <Route
        element={
          <RequireAuth>
            <ProfileSetupPage />
          </RequireAuth>
        }
        path="/profile-setup"
      />
      <Route
        element={
          <RequireAuth>
            <AppShell />
          </RequireAuth>
        }
        path="/app">
        <Route element={<DashboardPage />} index />
        <Route element={<PlansPage />} path="plans" />
        <Route element={<PlanDetailPage />} path="plans/:planId" />
        <Route element={<WorkoutPage />} path="workouts/:workoutId" />
        <Route element={<ExerciseLibraryPage />} path="exercises" />
        <Route element={<ExercisePage />} path="exercises/:exerciseId" />
        <Route element={<CoachPage />} path="coach" />
        <Route element={<Navigate replace to="/app/exercises" />} path="progress" />
        <Route element={<ProfilePage />} path="profile" />
      </Route>
      <Route element={<Navigate replace to="/" />} path="*" />
    </Routes>
  );
}
