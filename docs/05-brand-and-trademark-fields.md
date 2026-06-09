# Brand And Trademark Fields

本文档定义平台仓库从源码开始使用的正式客户可见品牌字段。

## 1. 决策

官网、客户控制台、管理员后台、license、部署向导、服务器管理 Agent 的默认品牌字段统一为：

```text
bairui
```

## 2. Required Fields

平台源码后续必须提供这些品牌字段：

- `brand_key`: `bairui`
- `trademark_name`: `bairui`
- `logo_text`: `bairui`
- `product_name`: `bairui Agent OS`

## 3. Boundary

工程名可以保留：

- `MOXI-cloud-agent`：平台和服务器管理仓库；
- `Hermes`：客户侧 Agent OS 后端内核。

但客户可见的默认品牌、商标和 logo 字段必须是 `bairui`。

## 4. First Implementation Target

后续创建 `apps/web` 源码时，应先在全局配置中实现：

```ts
export const brand = {
  key: "bairui",
  trademarkName: "bairui",
  logoText: "bairui",
  productName: "bairui Agent OS",
};
```
