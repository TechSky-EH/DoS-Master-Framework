#!/bin/bash
# DoS Master Framework - Installation Test Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║            DoS Master Framework - Installation Test             ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo

print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

TESTS_PASSED=0
TESTS_FAILED=0

run_test() {
    local test_name="$1"
    local test_command="$2"
    
    print_test "$test_name"
    
    if eval "$test_command" >/dev/null 2>&1; then
        print_pass "$test_name"
        ((TESTS_PASSED++))
        return 0
    else
        print_fail "$test_name"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Test 1: Check if dmf command exists
run_test "DMF command availability" "command -v dmf"

# Test 2: Check dmf version
run_test "DMF version check" "timeout 10 dmf --version"

# Test 3: Check help system
run_test "DMF help system" "timeout 10 dmf --help"

# Test 4: Check attack listing
run_test "Attack listing" "timeout 10 dmf --list-attacks"

# Test 5: Check validation
run_test "Installation validation" "timeout 15 dmf --validate"

# Test 6: Test dry-run capability
print_test "Dry-run functionality test"
if timeout 30 dmf --target 127.0.0.1 --attack icmp_flood --duration 5 --dry-run >/dev/null 2>&1; then
    print_pass "Dry-run functionality test"
    ((TESTS_PASSED++))
else
    print_fail "Dry-run functionality test"
    ((TESTS_FAILED++))
fi

# Test 7: Check system tools
TOOLS=("hping3" "nmap" "tcpdump" "python3")
for tool in "${TOOLS[@]}"; do
    run_test "System tool: $tool" "command -v $tool"
done

# Test 8: Check Python environment
print_test "Python environment check"
if dmf --validate 2>&1 | grep -q "Framework Imports.*Available"; then
    print_pass "Python environment check"
    ((TESTS_PASSED++))
else
    print_fail "Python environment check"
    ((TESTS_FAILED++))
fi

# Test 9: Web interface basic test (quick)
print_test "Web interface basic test"
if timeout 5 bash -c 'dmf --web-ui --port 18080 >/dev/null 2>&1 &
    sleep 2
    curl -s http://localhost:18080 >/dev/null 2>&1
    kill %1 2>/dev/null' 2>/dev/null; then
    print_pass "Web interface basic test"
    ((TESTS_PASSED++))
else
    print_fail "Web interface basic test"
    ((TESTS_FAILED++))
fi

# Summary
echo
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                           Test Summary                           ║"
echo "╚══════════════════════════════════════════════════════════════════╝"

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
echo "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo
    print_pass "🎉 ALL TESTS PASSED! Installation is working perfectly."
    echo
    echo "You can now use DoS Master Framework:"
    echo "  dmf --help                    # Show help"
    echo "  dmf --list-attacks           # List available attacks"
    echo "  dmf --target IP --attack TYPE --dry-run  # Safe testing"
    echo "  dmf --web-ui                 # Start web interface"
    
elif [ $TESTS_FAILED -le 2 ]; then
    echo
    print_info "✅ Installation is mostly working with $TESTS_FAILED minor issues."
    echo "The framework should be functional for basic use."
    
else
    echo
    print_fail "❌ Installation has significant issues ($TESTS_FAILED failures)."
    echo "Consider running the installation script again:"
    echo "  chmod +x scripts/install.sh"
    echo "  ./scripts/install.sh"
fi

echo
echo "For help and documentation:"
echo "  dmf --help"
echo "  dmf --validate"

exit $TESTS_FAILED