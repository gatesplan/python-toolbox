# Python Coding Protocol for Agent
- 이 문서는 에이전트의 원활하고 균일한 Python 코딩을 위한 프로토콜이다.
- 모든 에이전트는 Python 언어 사용시 이 코딩 프로토콜을 준수해야 한다.
- 이 파일은 루트 폴더의 중앙 지침이므로 에이전트는 절대 이 파일을 수정하지 않는다.

## 중요 규칙
- 하나의 파일은 오직 하나의 함수 또는 하나의 클래스만 포함한다.
- 모듈 클래스의 파일명과 클래스명은 CamelCase로 작성한다.
- 예외 클래스는 책임 모듈 폴더 아래에 위치한다.
- 클래스는 항상 단일 책임 원칙을 따른다.

## 문서화 규칙
- 모든 문서화는 `for-agent-moduleinfo.md` 파일 작성으로 충분하다.
- 코드 내에서는 한줄 주석(`#`)만 사용한다.
- Docstring(""" """), 멀티라인 주석, 함수/클래스 설명 주석 등 모든 문서화 주석은 작성하지 않거나 한 줄로 간단히 쓴다.
- 코드의 동작이나 구조 설명은 `for-agent-moduleinfo.md`에만 작성한다.

### 코드 예시
```python
# 사용자 인증을 처리하는 서비스
class AuthService:
    def __init__(self, token_manager):
        self.token_manager = token_manager

    def login(self, username, password):
        """"""
        if not username or not password:
            raise ValueError("Invalid credentials")
        token = self.token_manager.generate(username)
        return token

    def validate_token(self, token):
        return self.token_manager.verify(token)

    def logout(self, token):
        self.token_manager.revoke(token)
```
