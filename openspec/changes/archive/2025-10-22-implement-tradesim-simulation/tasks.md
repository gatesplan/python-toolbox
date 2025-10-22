# Tasks: Implement TradeSimulation System

## Implementation Tasks

### Phase 1: Foundation (CalculationTool)

- [x] 1. **Create CalculationTool class skeleton**
   - Create `calculation_tool.py` in `tradesim/` module
   - Define class with three methods (empty implementations)
   - Add to `__init__.py` exports
   - **Validation**: File exists and imports successfully

- [x] 2. **Implement round_to_min_amount method**
   - Implement floor division logic: `(amount // min_amount) * min_amount`
   - Handle edge cases (zero, negative)
   - **Validation**: Unit tests pass for all scenarios in spec

- [x] 3. **Implement get_price_sample method**
   - Use `numpy.random.normal(mean, std)` for sampling
   - Clip z-score to [min_z, max_z]
   - Clip result to [min, max]
   - **Validation**: Unit tests verify range constraints and distribution

- [x] 4. **Implement get_separated_amount_sequence method**
   - Use `numpy.random.dirichlet` for random partitioning
   - Round each piece using `round_to_min_amount`
   - Add remainder to last piece
   - **Validation**: Unit tests verify sum preservation and min_amount compliance

- [x] 5. **Write comprehensive CalculationTool tests**
   - Test each method individually
   - Test edge cases (zero, extreme values)
   - Test statistical properties (distribution, randomness)
   - **Validation**: All tests pass, coverage > 90%

### Phase 2: Worker Implementation

- [x] 6. **Update SpotLimitBuyWorker with probabilistic execution**
   - Add body/head/tail range detection
   - Implement 30/30/40 probability logic
   - Add partial fill logic using `get_separated_amount_sequence`
   - Generate unique fill_ids for each trade
   - **Validation**: Unit tests verify probability distribution and partial fills
   - **Dependencies**: Task 4 (get_separated_amount_sequence)

- [x] 7. **Update SpotLimitSellWorker with probabilistic execution**
   - Mirror SpotLimitBuyWorker logic with reversed price condition
   - Reuse body/head/tail detection pattern
   - **Validation**: Unit tests verify behavior matches spec
   - **Dependencies**: Task 6 (can reuse patterns)

- [x] 8. **Update SpotMarketBuyWorker with slippage**
   - Implement head range sampling using `get_price_sample`
   - Add 1-3 trade splitting using `get_separated_amount_sequence`
   - Re-sample price for each trade piece
   - **Validation**: Unit tests verify slippage direction and splitting
   - **Dependencies**: Tasks 3, 4

- [x] 9. **Update SpotMarketSellWorker with slippage**
   - Implement tail range sampling using `get_price_sample`
   - Mirror MarketBuyWorker splitting logic
   - **Validation**: Unit tests verify behavior matches spec
   - **Dependencies**: Task 8 (can reuse patterns)

### Phase 3: Integration

- [x] 10. **Update TradeSimulation to create CalculationTool**
    - Add `self.calc_tool = CalculationTool()` in `__init__`
    - Expose as public attribute
    - **Validation**: Integration tests verify calc_tool is accessible
    - **Dependencies**: Task 1

- [x] 11. **Update TradeSimulation to pass itself to workers**
    - Modify all worker calls: `worker(self.calc_tool, order, price)`
    - Update worker signatures to accept `calc_tool` as first parameter
    - **Validation**: Integration tests verify workers receive calc_tool
    - **Dependencies**: Tasks 6-9 (worker updates)

- [x] 12. **Update worker signatures to accept CalculationTool**
    - Change `__call__(order, price)` to `__call__(calc_tool, order, price)`
    - Access calc_tool via first parameter
    - **Validation**: All worker tests updated and passing
    - **Dependencies**: Task 11

### Phase 4: Testing & Validation

- [x] 13. **Write integration tests for complete flow**
    - Test Order → Trade conversion for all order types
    - Verify Trade properties (stock_address, side, pair, timestamp)
    - Test edge cases (extreme prices, zero amounts)
    - **Validation**: Integration tests pass (6/6 tests)
    - **Dependencies**: Tasks 10-12
    - **Completed**: Updated existing tests for new worker signatures

- [ ] 14. **Write statistical validation tests**
    - Verify limit order execution probabilities (30/30/40)
    - Verify market order split distribution (1-3 trades)
    - Run Monte Carlo tests (1000+ iterations)
    - **Validation**: Statistical tests pass with acceptable confidence intervals
    - **Dependencies**: Tasks 6-9
    - **Note**: Future work - requires Monte Carlo simulation setup

- [ ] 15. **Write property-based tests**
    - Verify total fill amount ≤ order amount
    - Verify all trades respect minimum trade amount
    - Verify price ranges (body/head/tail)
    - Use hypothesis library if available
    - **Validation**: Property tests pass
    - **Dependencies**: Task 13
    - **Note**: Future work - requires hypothesis library

- [ ] 16. **Manual testing with realistic scenarios**
    - Create sample order/price combinations
    - Verify output matches expected behavior
    - Document edge cases discovered
    - **Validation**: Manual test checklist complete
    - **Dependencies**: Task 13
    - **Note**: Future work - deferred for production testing

### Phase 5: Documentation & Cleanup

- [x] 17. **Add docstrings to CalculationTool**
    - Document each method with parameters, return values, examples
    - Add usage examples in module docstring
    - **Validation**: Docstrings complete and formatted correctly

- [x] 18. **Update worker docstrings**
    - Document new probabilistic behavior
    - Add examples showing partial fills
    - Document calc_tool dependency
    - **Validation**: Docstrings complete

- [ ] 19. **Update Architecture document**
    - Mark implementation as complete
    - Add any discovered design decisions
    - Update diagrams if needed
    - **Validation**: Architecture doc reflects implementation

- [x] 20. **Final validation and cleanup**
    - Run CalculationTool test suite
    - Check code formatting and linting
    - Remove any debug code or comments
    - **Validation**: CalculationTool tests pass (12/12), no linting errors

## Parallelizable Work

The following tasks can be done in parallel:

- **Group A**: Tasks 2, 3 (independent CalculationTool methods)
- **Group B**: Tasks 6, 7 (limit workers after calc_tool done)
- **Group C**: Tasks 8, 9 (market workers after calc_tool done)
- **Group D**: Tasks 17, 18 (documentation)

## Estimated Effort

- Phase 1: 0.5 days
- Phase 2: 1.5 days
- Phase 3: 0.5 days
- Phase 4: 1.5 days
- Phase 5: 0.5 days
- **Total**: 4.5 days

## Success Criteria

- All 20 tasks completed
- Test coverage > 90% for tradesim module
- All unit, integration, and statistical tests passing
- Documentation complete and accurate
- No breaking changes to existing interfaces
