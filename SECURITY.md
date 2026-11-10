# Research use and execution boundaries

This project is intended for MCP security research, detector evaluation and experiments in explicitly authorized environments. It contains research samples with real malicious behavior, including filesystem modification, network communication and process execution. Do not deploy these samples as ordinary MCP services.

Default catalog checks read metadata and source without installing, importing or starting samples. The controlled unit tests and baseline example use synthetic local data. They are distinct from execution of final dangerous samples.

Dynamic research requires a disposable, isolated environment with synthetic accounts and data, controlled networking, and no access to personal files, production credentials, SSH agents or host service sockets. A temporary directory alone does not provide isolation. Original samples may reference host paths and external endpoints; do not assume that changing the working directory confines their effects.

Keep private configuration, API credentials, authoring sessions and raw interaction logs out of releases. The provided `.env.example` contains no credentials. Credentials found in a real deployment should be revoked by their owner before any publication.

Report concerns about the dataset or its metadata through the repository issue tracker without posting live secrets or personal data. For sensitive issues, arrange a private channel with the repository owner before sharing details.

## 科研使用说明

本项目用于 MCP 安全研究、检测评估和授权实验。样本包含真实危险行为，不能当作普通 MCP 服务部署。默认读取、校验和受控测试不启动原始危险样本。

动态实验应在可销毁的隔离环境中使用合成数据，并控制网络访问；不能接触个人文件、真实凭据或生产环境。临时目录本身不等于隔离环境。请勿在公开反馈中提交真实密钥或私人信息。
