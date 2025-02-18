vim.g.ale_sign_error = '⤫'
vim.g.ale_sign_warning = '⚠'

vim.g.ale_rust_cargo_use_clippy = 1

vim.g.ale_linters = {
	go = {'golangci-lint'},
}

vim.g.ale_go_golangci_lint_options = '--enable-all'
vim.g.ale_go_golangci_lint_package = 1

vim.g.ale_fixers = {
	['*'] = {'remove_trailing_lines', 'trim_whitespace'},
	python = {'black', 'isort'},
	rust = {'rustfmt'},
}

vim.g.ale_python_black_options = '--line-length 80'
vim.g.ale_python_mypy_options = '–ignore-missing-imports'

vim.g.ale_fix_on_save = 1

vim.g.ale_nasm_nasm_options = '-felf64 -Werror'
