#!/bin/bash
# Quick test script for DoS Master Framework

echo "🧪 Testing DoS Master Framework Installation"
echo "=============================================="

# Test 1: Command exists
echo -n "Testing dmf command... "
if command -v dmf >/dev/null 2>&1; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
    exit 1
fi

# Test 2: Version check
echo -n "Testing version check... "
if timeout 10 dmf --version >/dev/null 2>&1; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
fi

# Test 3: Help system
echo -n "Testing help system... "
if timeout 10 dmf --help >/dev/null 2>&1; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
fi

# Test 4: List attacks
echo -n "Testing attack listing... "
if timeout 10 dmf --list-attacks >/dev/null 2>&1; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
fi

# Test 5: Safe dry run
echo -n "Testing safe dry-run... "
if timeout 30 dmf --target 127.0.0.1 --attack icmp_flood --duration 3 --dry-run >/dev/null 2>&1; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
fi

echo
echo "🎉 Basic tests completed!"
echo
echo "Next steps:"
echo "  dmf --validate              # Detailed validation"
echo "  dmf --list-attacks         # See available attacks"  
echo "  dmf --target 127.0.0.1 --attack icmp_flood --duration 5 --dry-run"
echo
echo "⚠️  Remember: Always use --dry-run first!"