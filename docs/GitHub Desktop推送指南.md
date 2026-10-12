# GitHub Desktop 推送指南（图文步骤版）

> 适用：已装 GitHub Desktop 3.6+，GitHub 用户名 `QKL-queen`，目标仓库 `opto-data-assistant`。
> 全程不需要命令行，所有操作在 GitHub Desktop 窗口里点按钮完成。

---

## 第 1 步：打开 GitHub Desktop 并登录

1. 开始菜单搜索 **GitHub Desktop**，打开；
2. 打开后如果右上角是 “Sign in”，点击它：
   - 窗口会弹出 **Sign in to GitHub.com**，点 **Continue with browser**；
   - 浏览器打开 GitHub 登录页，输入你的账号密码（`QKL-queen`）登录；
   - 浏览器提示 “Open GitHub Desktop?” 时点 **打开**；
   - 回到 GitHub Desktop，点 **Continue**，再点 **Finish**（可跳过贡献设置）。
3. 右上角显示你的头像/用户名 = 登录成功。

> 如果界面已经是登录状态（右上角有头像），直接进入第 2 步。

## 第 2 步：导入项目文件夹

1. 菜单栏 **File → Add Local Repository…**；
2. 弹出选择窗口，点击 **Choose…**，选择：
   ```
   C:\Users\QKL\Doubao\chats\2026-10-05\new-chat\光电实验数据处理助手
   ```
3. 因为该文件夹还不是 Git 仓库，GitHub Desktop 会提示：
   > *This directory does not appear to be a Git repository. Would you like to create a repository here instead?*
   
   点 **Create a repository**；
4. 弹出的窗口里：
   - **Name** 改为：`opto-data-assistant`（不要用中文名，方便开源展示）；
   - **Local path** 保持原文件夹即可；
   - **Git ignore** 保持 **None**（项目里已有 .gitignore）；
   - 点 **Create repository**。

## 第 3 步：提交（Commit）

窗口左侧会列出所有将被提交的文件（`app.py`、`core/`、`README.md`、`docs/`、`examples/`…，`venv/` 已被 .gitignore 自动排除，不会出现）：

1. 确认文件列表里**没有** `venv` 文件夹；
2. 左下角 **Summary** 填：`光电实验数据处理助手 v1.0：公式计算/数据拟合/不确定度/报告生成`；
3. 点 **Commit to main**。

## 第 4 步：发布到 GitHub（开源）

1. 点窗口右上角蓝色按钮 **Publish repository**；
2. 弹窗里 **Name** 确认是 `opto-data-assistant`；
3. **Keep this code private** 复选框 **不要勾选**（招新要求公开开源）；
4. 点 **Publish repository**。

发布完成后，GitHub Desktop 顶部会显示分支 `main` 和 “✓ 已发布” 提示。

## 第 5 步：验证开源成功

1. 浏览器打开：
   ```
   https://github.com/QKL-queen/opto-data-assistant
   ```
2. 能看到 README 预览、代码文件列表即成功；
3. 把该链接填进 README 末尾「作者」栏（可选）。

---

## 之后更新代码（重要，以后每次都用）

1. 改完代码回到 GitHub Desktop，左侧会出现“更改”列表；
2. Summary 填一句说明，点 **Commit to main**；
3. 点顶部 **Push origin**（或按钮变成 **Fetch origin** 旁边的 ↑）。

## 常见问题

| 现象 | 处理 |
|---|---|
| 登录时浏览器打不开 | 确认已登录 github.com；重新点 Sign in → Continue with browser |
| Add Local Repository 后没弹创建提示 | 说明该文件夹已是 Git 仓库（之前 init 过）：直接进行第 3 步；若想重来，删除文件夹里的 `.git` 再导入 |
| 提交列表里有 venv/ | 检查项目根目录 .gitignore 是否存在（已提供）；删掉列表中的 venv 条目不会影响本地文件 |
| Publish 按钮是灰的 | 确认已 Commit 过一次（第 3 步完成） |
| 仓库名想改 | 网页 Settings → General → Repository name（改动后本地需重新关联，可咨询我） |

## 招新提交清单（最后检查）

- [ ] GitHub 仓库公开可访问：https://github.com/QKL-queen/opto-data-assistant
- [ ] 个人简介（Word）已替换占位符：`docs/个人简介（招新材料）.docx`
- [ ] README 作者栏已填姓名/学号/GitHub 链接
- [ ] 演示视频（3 分钟，脚本见 `docs/设计制作流程与修缮指南.md` 8.3）
- [ ] 压缩包：源代码 + README/演示 + 个人简介 + 仓库链接 → 邮件
      主题：`学号—姓名—项目名称`，发至 szu.cpoe.ilab@outlook.com（以通知为准）
