# GitHub 上传操作手册（一步步带你推）

> 适用情况：电脑已安装 Git for Windows（本手册配套），GitHub 账号**尚未注册**，
> 目标：把《光电实验数据处理助手》项目推送到你的 GitHub 仓库并开源。

全程共 6 步，前 3 步在本机命令行完成，第 4 步需要你在浏览器操作一次。
每步后面都写了「检查」方法，卡住时对照第 7 节排查。

---

## 第 1 步：确认 Git 已安装

打开 PowerShell（开始菜单搜索 “PowerShell” 或 “终端”），输入：

```powershell
git --version
```

看到类似 `git version 2.4x.x.windows.1` 即成功。
如果提示“无法将 git 项识别为…”，先**重新打开**一个 PowerShell 窗口再试
（新装的 Git 需要新窗口才能生效）。仍不行则执行：

```powershell
winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
```

---

## 第 2 步：注册 GitHub 账号（浏览器操作，约 3 分钟）

1. 打开 <https://github.com/signup>；
2. 填写：邮箱（建议用常用邮箱）、密码、**用户名（英文）**——这个用户名就是你的 GitHub 身份，后面代码地址里会有它；
3. 完成人机验证（拼图/选图），去邮箱点验证链接；
4. 记下你的**用户名**，后面步骤都要用。

> 用户名建议：小写字母 + 数字，如 `zhangsan-opto`。

---

## 第 3 步：告诉 Git“你是谁”（一次性配置）

在 PowerShell 里执行（替换成你自己的信息）：

```powershell
git config --global user.name  "你的GitHub用户名"
git config --global user.email "你注册GitHub用的邮箱"
```

**检查：**

```powershell
git config --global user.name
git config --global user.email
```

能打印出刚才填的内容即成功。

---

## 第 4 步：在项目文件夹初始化仓库并提交

在 PowerShell 中进入项目目录（复制下面整条命令）：

```powershell
cd "C:\Users\QKL\Doubao\chats\2026-10-05\new-chat\光电实验数据处理助手"
git init
git add .
git commit -m "光电实验数据处理助手 v1.0：公式计算/数据拟合/不确定度/报告生成"
```

**检查：**

```powershell
git log --oneline
```

看到 `光电实验数据处理助手 v1.0 ...` 即提交成功。

> 说明：项目里已配好 `.gitignore`，会自动排除 `venv/`（虚拟环境）和缓存目录，
> 推上去的只有源代码与文档，体积小且干净。

---

## 第 5 步：在 GitHub 网页创建空仓库（浏览器操作）

1. 登录 GitHub，点右上角 **+** → **New repository**；
2. 仓库名（Repository name）填：`opto-data-assistant`
   （名字随意，但建议和项目相关、英文、小写）；
3. 可见性选 **Public**（招新要求开源）；
4. **不要**勾选 “Add a README file”、“Add .gitignore”、“Choose a license”
   （我们本地已经有了，勾了反而会冲突）；
5. 点 **Create repository**；
6. 创建成功后页面会显示一段带地址的命令。把地址复制下来，形如：
   - HTTPS 地址：`https://github.com/你的用户名/opto-data-assistant.git`
   - 或 SSH 地址：`git@github.com:你的用户名/opto-data-assistant.git`

> **新手建议用 HTTPS 地址**，推送时自动弹出浏览器登录，最省事。

---

## 第 6 步：关联远程仓库并推送

回到 PowerShell（还在项目目录里），把地址换成你刚复制的：

```powershell
git remote add origin https://github.com/你的用户名/opto-data-assistant.git
git branch -M main
git push -u origin main
```

第一次推送会弹出 **GitHub 登录窗口**（或浏览器页面），按提示登录授权即可；
之后每次推送不再需要。

**检查：**

```powershell
git remote -v
```

看到 `origin` 指向你的仓库地址即成功；再到浏览器打开
`https://github.com/你的用户名/opto-data-assistant`，
能看到 README、代码文件就说明**开源成功**。

---

## 第 7 步：更新个人信息并提交招新材料

1. 用 Word 打开 `docs/个人简介（招新材料）.docx`，把〔姓名〕〔学号〕〔班级〕〔邮箱〕等占位符替换成真实信息；
2. 把改动同步推上去（可选）：

```powershell
git add .
git commit -m "补充个人简介"
git push
```

3. 按招新通知整理 `.zip`：项目源代码 + README/演示材料 + 个人简介 + GitHub 链接；
4. 邮件主题：`学号—姓名—项目名称`，发送至 `szu.cpoe.ilab@outlook.com`（以通知为准）。

---

## 常见问题排查

| 现象 | 原因与解决 |
|---|---|
| `git` 不是内部或外部命令 | Git 没装或没生效：重开 PowerShell；或执行第 1 步的 winget 命令 |
| `fatal: not a git repository` | 不在项目目录：先 `cd` 进项目文件夹再执行 |
| `git push` 提示认证失败 | 用 HTTPS 推送首次会弹窗登录；若用的是 SSH 地址且没配密钥，改用 HTTPS 地址重来 |
| `remote origin already exists` | 重复添加：先 `git remote remove origin` 再添加 |
| 网页上没看到文件 | 推送成功后网页刷新；确认 push 无报错 |
| 想改仓库名/描述 | 网页仓库 Settings → General → Repository name |

---

## 成功后

把仓库链接填进 README 末尾「作者」一栏，再录一个 3 分钟演示视频（脚本见
`docs/设计制作流程与修缮指南.md` 第 8.3 节），招新材料就齐了。

如果哪一步卡住，直接把报错原文发给我，我帮你定位。
