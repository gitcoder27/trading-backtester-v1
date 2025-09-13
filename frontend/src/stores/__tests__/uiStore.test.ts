import { describe, it, expect, beforeEach } from 'vitest';
import { useUIStore } from '../../stores/uiStore';

describe('uiStore', () => {
  beforeEach(() => {
    useUIStore.setState({ sidebarOpen: true, theme: 'dark', notifications: [] });
  });

  it('toggles and sets sidebar', () => {
    useUIStore.getState().toggleSidebar();
    expect(useUIStore.getState().sidebarOpen).toBe(false);
    useUIStore.getState().setSidebarOpen(true);
    expect(useUIStore.getState().sidebarOpen).toBe(true);
  });

  it('manages notifications', () => {
    useUIStore.getState().addNotification({ type: 'success', title: 'Hi', message: 'There' });
    expect(useUIStore.getState().notifications.length).toBe(1);
    const id = useUIStore.getState().notifications[0].id;
    useUIStore.getState().removeNotification(id);
    expect(useUIStore.getState().notifications.length).toBe(0);
    useUIStore.getState().addNotification({ type: 'info', title: 'x' });
    useUIStore.getState().clearNotifications();
    expect(useUIStore.getState().notifications).toEqual([]);
  });
});

