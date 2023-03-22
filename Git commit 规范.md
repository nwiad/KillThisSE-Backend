# Git commit 规范

20230322 KS

## 0 !!!! 注意往`dev分支`上push !!!

## 1  **commit message格式**

```text
<type>(<scope>): <subject>
```

eg. feat(Controller):用户查询接口开发

#### 1.1 **type(必须)**

用于说明git commit的类别，只允许使用下面的标识。

- **feat**：新功能（feature）。

- **fix/to**：修复bug，可以是QA发现的BUG，也可以是研发自己发现的BUG。

  - fix：产生diff并自动修复此问题。适合于一次提交直接修复问题

  - to：只产生diff不自动修复此问题。适合于多次提交。最终修复问题提交时使用fix

- **docs**：文档（documentation）。

- **style**：格式（不影响代码运行的变动）。

- **refactor**：重构（即不是新增功能，也不是修改bug的代码变动）。

- **perf**：优化相关，比如提升性能、体验。

- **test**：增加测试。

- **chore**：构建过程或辅助工具的变动。

- **revert**：回滚到上一个版本。

- **merge**：代码合并。

- **sync**：同步主线或分支的Bug。



#### 1.2 **scope(可选)**

scope用于说明 commit 影响的范围，比如数据层、控制层、视图层等等，视项目不同而不同。

例如在Angular，可以是location，browser，compile，compile，rootScope， ngHref，ngClick，ngView等。如果你的修改影响了不止一个scope，你可以使用*代替。



#### 1.3 **subject(必须)**

subject是commit目的的简短描述，不超过50个字符。 建议使用中文。

- 结尾不加句号或其他标点符号。
- 根据以上规范git commit message将是如下的格式：

```text
fix(DAO):用户查询缺少username属性 
feat(Controller):用户查询接口开发
```

以上就是我们梳理的git commit规范，那么我们这样规范git commit到底有哪些好处呢？

- 便于程序员对提交历史进行追溯，了解发生了什么情况。
- 一旦约束了commit message，意味着我们将慎重的进行每一次提交，不能再一股脑的把各种各样的改动都放在一个git commit里面，这样一来整个代码改动的历史也将更加清晰。
- 格式化的commit message才可以用于自动化输出Change log。

## 2 [必要时使用] 完整commit

Commit message 可以包括三个部分：Header，Body 和 Footer。

（1 节中其实是只写了Header

```bash
<type>(<scope>): <subject>
// 空一行
<body>
// 空一行
<footer>
```

### 2.1 Body

Body 部分是对本次 commit 的详细描述，可以分成多行。下面是一个范例。

> ```bash
> More detailed explanatory text, if necessary.  Wrap it to 
> about 72 characters or so. 
> 
> Further paragraphs come after blank lines.
> 
> - Bullet points are okay, too
> - Use a hanging indent
> ```

注意：

（1）使用第一人称现在时，比如使用`change`而不是`changed`或`changes`。

（2）应该说明代码变动的动机，以及与以前行为的对比。

### 2.2 Footer

Footer 部分只用于两种情况。

**（1）不兼容变动**

如果当前代码与上一个版本不兼容，则 Footer 部分以`BREAKING CHANGE`开头，后面是对变动的描述、以及变动理由和迁移方法。

> ```bash
> BREAKING CHANGE: isolate scope bindings definition has changed.
> 
>     To migrate the code follow the example below:
> 
>     Before:
> 
>     scope: {
>       myAttr: 'attribute',
>     }
> 
>     After:
> 
>     scope: {
>       myAttr: '@',
>     }
> 
>     The removed `inject` wasn't generaly useful for directives so there should be no code using it.
> ```

**2）关闭 Issue**

如果当前 commit 针对某个issue，那么可以在 Footer 部分关闭这个 issue 。

> ```bash
> Closes #234
> ```

也可以一次关闭多个 issue 。

> ```bash
> Closes #123, #245, #992
> ```





##### 参考：

https://zhuanlan.zhihu.com/p/182553920

[Commit message 和 Change log 编写指南 - 阮一峰的网络日志 (ruanyifeng.com)](http://ruanyifeng.com/blog/2016/01/commit_message_change_log.html)