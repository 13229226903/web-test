"""SEO回归 — 重定向页面：访问源URL后验证重定向到目标URL且页面正常打开。"""
import pytest, allure
from playwright.sync_api import Page
from conftest import allure_screenshot


REDIRECTS = [
    pytest.param("/tools/red-eye-remover", "/face-editor/red-eye-remover", id="red-eye-remover"),
    pytest.param("/tools/photo-blemish-remover", "/face-editor/photo-blemish-remover", id="photo-blemish-remover"),
    pytest.param("/tools/ai-face-smoother", "/tools/ai-image-smoother", id="ai-face-smoother"),
    pytest.param("/ai-replace/body-editor", "/body-editor", id="body-editor"),
    pytest.param("/fr/privacy-policy", "/privacy-policy", id="privacy-policy-fr"),
    pytest.param("/de/term-of-use", "/term-of-use", id="term-of-use-de"),
]


@pytest.mark.regression
@allure.epic("主流程回归")
@allure.feature("SEO回归")
class TestRedirectSEO:

    @pytest.mark.parametrize("src_path,dst_path", REDIRECTS)
    def test_redirect(self, page: Page, base_url: str, src_path, dst_path):
        src_name = src_path.rsplit("/", 1)[-1]
        allure.dynamic.title(f"[P0] {src_name} → {dst_path}")

        # 访问源 URL，捕获重定向链
        response = page.goto(f"{base_url}{src_path}", timeout=60000)
        page.wait_for_timeout(5000)

        # 记录重定向过程
        redirect_chain = []
        req = response.request
        while req:
            redirect_chain.append(req.url.replace(base_url, ""))
            req = req.redirected_from
        redirect_chain.reverse()
        allure.attach(
            f"源URL: {src_path}\n目标URL: {dst_path}\n实际链路: {' → '.join(redirect_chain)}",
            name="重定向链路",
            attachment_type=allure.attachment_type.TEXT,
        )

        # 断言重定向到目标 URL
        final_url = page.url
        assert dst_path in final_url, \
            f"应从 {src_path} 重定向到 {dst_path}，实际链路: {' → '.join(redirect_chain)}"

        # 截图（含URL信息）
        allure_screenshot(page, f"重定向-{src_name}-{final_url.replace(base_url, '')[:60]}")

        # 断言页面正常打开
        assert page.title(), f"重定向后页面应能正常打开，URL: {final_url}"
        body = page.locator("body").inner_text()
        assert len(body) > 100, f"页面内容过少（{len(body)}字符），可能加载失败"
