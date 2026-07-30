import { Download, RefreshCw, WifiOff, X } from 'lucide-react';
import { useRegisterSW } from 'virtual:pwa-register/react';

export function PwaPrompt() {
  const {
    offlineReady: [offlineReady, setOfflineReady],
    needRefresh: [needRefresh, setNeedRefresh],
    updateServiceWorker,
  } = useRegisterSW();

  if (!offlineReady && !needRefresh) {
    return null;
  }

  const close = () => {
    setOfflineReady(false);
    setNeedRefresh(false);
  };

  return (
    <aside aria-live="polite" className="pwa-toast">
      <span className="pwa-toast__icon">
        {needRefresh ? <RefreshCw size={20} /> : <WifiOff size={20} />}
      </span>
      <div>
        <strong>{needRefresh ? '发现新版本' : '离线能力已就绪'}</strong>
        <p>
          {needRefresh
            ? '刷新后即可使用最新的 FitFlow。'
            : '网络中断时仍可打开应用外壳。'}
        </p>
      </div>
      {needRefresh ? (
        <button
          className="pwa-toast__action"
          onClick={() => void updateServiceWorker(true)}
          type="button">
          <Download size={16} />
          更新
        </button>
      ) : null}
      <button
        aria-label="关闭提示"
        className="pwa-toast__close"
        onClick={close}
        type="button">
        <X size={17} />
      </button>
    </aside>
  );
}
