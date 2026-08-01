# FitFlow AI React PWA

`web/` 是 FitFlow AI 唯一前端，使用 React、TypeScript、Vite 和 PWA。
手机端是主要设计目标，电脑端提供响应式布局。

## 本地开发

```powershell
cd F:\python_project\FitFlow_AI\web
npm install
npm run dev
```

## 生产构建

```powershell
npm run build
```

前端通过 HTTP 调用 FastAPI，不保存 DashScope Key，也不执行后端安全规则。
