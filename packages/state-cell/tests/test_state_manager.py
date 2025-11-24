import pytest
from state_cell import StateCell, StateManager


class MockCell(StateCell):
    """StateManager 테스트용 Mock Cell"""

    def __init__(self):
        super().__init__()
        self._state = 0

    def update(self, value, **kwargs):
        # 간단한 로직: value가 50 이상이면 상태 1, 아니면 0
        if value >= 50:
            self._state = 1
        else:
            self._state = 0
        return self._state

    def get_state(self):
        return self._state

    def reset(self):
        self._state = 0


class TestStateManagerInit:
    """StateManager 초기화 테스트"""

    def test_init_without_states(self):
        # states 없이 초기화
        cell = MockCell()
        manager = StateManager(cell)

        assert manager._cell is cell
        assert manager.states is None
        assert manager._current_state is None
        assert manager._original_initial is None
        assert manager._listeners == []

    def test_init_with_states(self):
        # states와 initial 지정
        cell = MockCell()
        manager = StateManager(cell, states=['LOW', 'HIGH'], initial='LOW')

        assert manager.states == ['LOW', 'HIGH']
        assert manager._current_state == 'LOW'
        assert manager._original_initial == 'LOW'


class TestStateManagerUpdate:
    """StateManager update 테스트"""

    def test_update_without_states(self):
        # states 없이 사용 (인덱스 반환)
        cell = MockCell()
        manager = StateManager(cell)

        result = manager.update(30)
        assert result == 0

        result = manager.update(60)
        assert result == 1

    def test_update_with_states(self):
        # states로 매핑
        cell = MockCell()
        manager = StateManager(cell, states=['LOW', 'HIGH'], initial='LOW')

        result = manager.update(30)
        assert result == 'LOW'

        result = manager.update(60)
        assert result == 'HIGH'

    def test_update_state_persistence(self):
        # 상태가 올바르게 유지되는지
        cell = MockCell()
        manager = StateManager(cell, states=['LOW', 'HIGH'], initial='LOW')

        manager.update(60)
        assert manager.get_state() == 'HIGH'

        manager.update(70)
        assert manager.get_state() == 'HIGH'


class TestStateManagerObserver:
    """StateManager Observer 패턴 테스트"""

    def test_listener_called_on_state_change(self):
        # 상태 변경 시 listener 호출
        cell = MockCell()
        manager = StateManager(cell, states=['LOW', 'HIGH'], initial='LOW')

        changes = []
        def listener(old, new):
            changes.append((old, new))

        manager.add_listener(listener)

        manager.update(30)  # LOW -> LOW (변경 없음)
        assert len(changes) == 0

        manager.update(60)  # LOW -> HIGH (변경!)
        assert len(changes) == 1
        assert changes[0] == ('LOW', 'HIGH')

        manager.update(70)  # HIGH -> HIGH (변경 없음)
        assert len(changes) == 1

        manager.update(20)  # HIGH -> LOW (변경!)
        assert len(changes) == 2
        assert changes[1] == ('HIGH', 'LOW')

    def test_multiple_listeners(self):
        # 여러 listener 등록
        cell = MockCell()
        manager = StateManager(cell, states=['LOW', 'HIGH'], initial='LOW')

        calls1 = []
        calls2 = []

        manager.add_listener(lambda old, new: calls1.append((old, new)))
        manager.add_listener(lambda old, new: calls2.append((old, new)))

        manager.update(60)  # LOW -> HIGH

        assert len(calls1) == 1
        assert len(calls2) == 1

    def test_remove_listener(self):
        # listener 제거
        cell = MockCell()
        manager = StateManager(cell, states=['LOW', 'HIGH'], initial='LOW')

        calls = []
        listener = lambda old, new: calls.append((old, new))

        manager.add_listener(listener)
        manager.update(60)  # 호출됨
        assert len(calls) == 1

        manager.remove_listener(listener)
        manager.update(20)  # 호출 안 됨
        assert len(calls) == 1


class TestStateManagerReset:
    """StateManager reset 테스트"""

    def test_reset_restores_initial_state(self):
        # reset 시 초기 상태 복원
        cell = MockCell()
        manager = StateManager(cell, states=['LOW', 'HIGH'], initial='LOW')

        manager.update(60)
        assert manager.get_state() == 'HIGH'

        manager.reset()
        assert manager.get_state() == 'LOW'

    def test_reset_does_not_notify(self):
        # reset 시 notify 하지 않음
        cell = MockCell()
        manager = StateManager(cell, states=['LOW', 'HIGH'], initial='LOW')

        calls = []
        manager.add_listener(lambda old, new: calls.append((old, new)))

        manager.update(60)  # notify 발생
        assert len(calls) == 1

        manager.reset()  # notify 발생 안 함
        assert len(calls) == 1

    def test_reset_calls_cell_reset(self):
        # reset이 내부 cell의 reset도 호출하는지
        cell = MockCell()
        manager = StateManager(cell, states=['LOW', 'HIGH'], initial='LOW')

        manager.update(60)
        assert cell.get_state() == 1

        manager.reset()
        assert cell.get_state() == 0


class TestStateManagerGetState:
    """StateManager get_state 테스트"""

    def test_get_state_returns_current_state(self):
        cell = MockCell()
        manager = StateManager(cell, states=['LOW', 'HIGH'], initial='LOW')

        assert manager.get_state() == 'LOW'

        manager.update(60)
        assert manager.get_state() == 'HIGH'
