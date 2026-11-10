import { Navigate, Route, Routes } from 'react-router-dom';
import AppShell from '../components/layout/AppShell';
import Alerts from '../pages/Alerts';
import ClientReport from '../pages/ClientReport';
import Diagnose from '../pages/Diagnose';
import Login from '../pages/Login';
import Runs from '../pages/Runs';
import Sites from '../pages/Sites';
import TemplateEditor from '../pages/TemplateEditor';
import { RequireAuth, RequirePermission } from './guards';

function Protected({ permission, children }: { permission: string; children: React.ReactNode }) {
  return (
    <RequireAuth>
      <AppShell>
        <RequirePermission permission={permission}>{children}</RequirePermission>
      </AppShell>
    </RequireAuth>
  );
}

export default function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Navigate to="/sites" replace />} />
      <Route path="/sites" element={<Protected permission="run:execute"><Sites /></Protected>} />
      <Route path="/templates/:id" element={<Protected permission="run:execute"><TemplateEditor /></Protected>} />
      <Route
        path="/snapshots/:snapshotId/diagnose/:templateId"
        element={<Protected permission="diagnose:run"><Diagnose /></Protected>}
      />
      <Route path="/runs" element={<Protected permission="run:execute"><Runs /></Protected>} />
      <Route path="/alerts" element={<Protected permission="candidate:apply"><Alerts /></Protected>} />
      <Route path="/client/report" element={<Protected permission="report:read"><ClientReport /></Protected>} />
      <Route path="*" element={<Navigate to="/sites" replace />} />
    </Routes>
  );
}
