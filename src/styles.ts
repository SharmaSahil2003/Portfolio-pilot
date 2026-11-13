import { createGlobalStyle, styled } from 'styled-components'

export const GlobalStyle = createGlobalStyle`
  @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
  :root { font-family: 'DM Sans', sans-serif; color: #f1f3ee; background: #0d1014; font-synthesis: none; text-rendering: optimizeLegibility; }
  * { box-sizing: border-box; }
  body { margin: 0; min-width: 320px; min-height: 100vh; }
  button, input, textarea { font: inherit; }
  button { cursor: pointer; }
  ::selection { background: #c6f36b; color: #12150e; }
`
export const Shell = styled.div`min-height:100vh; display:grid; grid-template-columns:minmax(0,1fr); background:#0d1014`
export const Sidebar = styled.aside`padding:27px 17px 20px; border-right:1px solid #252a30; display:flex; flex-direction:column; gap:32px; @media(max-width:900px){padding:24px 12px}`
export const Brand = styled.div`display:flex; align-items:center; gap:11px; padding:0 11px; font:800 17px Manrope,sans-serif; letter-spacing:-.7px; span{color:#c6f36b}@media(max-width:900px){justify-content:center;padding:0}`
export const BrandMark = styled.div`width:30px;height:30px;border-radius:10px;background:#c6f36b;color:#171b12;display:grid;place-items:center;font:800 15px Manrope,sans-serif;box-shadow:0 0 24px #c6f36b22`
export const NavGroup = styled.div`display:grid;gap:5px`
export const NavLabel = styled.div`padding:0 12px 9px;color:#6d747a;font:500 10px 'DM Mono',monospace;letter-spacing:1.3px;text-transform:uppercase;@media(max-width:900px){display:none}`
export const NavItem = styled.button<{ $active?: boolean }>`border:0;border-radius:9px;background:${p=>p.$active?'#1d2425':'transparent'};color:${p=>p.$active?'#c6f36b':'#989fa5'};height:42px;padding:0 12px;display:flex;align-items:center;gap:12px;text-align:left;font-size:13px;transition:.18s;&:hover{background:#1a2024;color:#eff1eb}svg{width:17px;height:17px}@media(max-width:900px){justify-content:center;padding:0;span{display:none}}`
export const SideBottom = styled.div`margin-top:auto;border-top:1px solid #252a30;padding:18px 6px 0;display:flex;align-items:center;gap:10px`
export const Avatar = styled.div`height:31px;width:31px;border-radius:50%;background:#343b40;color:#d8dfd1;display:grid;place-items:center;font-size:11px;font-weight:700;flex:none`
export const UserText = styled.div`min-width:0;flex:1;strong{display:block;font-size:12px;font-weight:600}small{display:block;margin-top:3px;color:#737b80;font-size:10px}@media(max-width:900px){display:none}`
export const Main = styled.main`min-width:0;width:min(1440px,100%);margin:0 auto;padding:0 42px 48px;@media(max-width:1100px){padding:0 25px 40px}@media(max-width:650px){padding:0 16px 28px}`
export const Topbar = styled.header`height:78px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #252a30;margin-bottom:34px`
export const Breadcrumb = styled.div`font:11px 'DM Mono',monospace;color:#777f85;span{color:#e4e9df}`
export const Actions = styled.div`display:flex;align-items:center;gap:10px`
export const IconButton = styled.button`width:35px;height:35px;border:1px solid #2c3237;background:#111519;color:#9aa29f;border-radius:9px;display:grid;place-items:center;&:hover{color:#f1f3ee;border-color:#505957}svg{width:16px;height:16px}`
export const PageHeader = styled.div`display:flex;align-items:flex-end;justify-content:space-between;gap:18px;margin-bottom:28px;@media(max-width:650px){align-items:flex-start;flex-direction:column}`
export const Eyebrow = styled.div`color:#c6f36b;font:11px 'DM Mono',monospace;letter-spacing:1px;text-transform:uppercase;margin-bottom:11px`
export const H1 = styled.h1`margin:0;color:#f1f3ee;font:700 clamp(25px,3vw,34px) Manrope,sans-serif;letter-spacing:-1.25px`
export const Muted = styled.p`margin:8px 0 0;color:#8a9297;font-size:13px;line-height:1.65`
export const PrimaryButton = styled.button`border:0;border-radius:8px;background:#c6f36b;color:#1a2112;font-weight:700;font-size:12px;padding:11px 15px;display:inline-flex;align-items:center;justify-content:center;gap:8px;transition:.18s;&:hover{background:#d4ff7a;transform:translateY(-1px)}&:disabled{opacity:.5;cursor:not-allowed}svg{width:15px;height:15px}`
export const SecondaryButton = styled.button`border:1px solid #333a3e;border-radius:8px;background:#171c20;color:#e0e5df;font-weight:600;font-size:11px;padding:9px 12px;display:inline-flex;align-items:center;justify-content:center;gap:7px;&:hover{border-color:#5c6965;background:#1d2426}svg{width:14px;height:14px}`
export const Grid = styled.div`display:grid;grid-template-columns:minmax(0,1fr);gap:18px;align-items:start`
export const Column = styled.div`display:grid;gap:18px;min-width:0`
export const Card = styled.section`background:#13181c;border:1px solid #272e32;border-radius:12px;overflow:hidden`
export const CardHead = styled.div`padding:17px 19px;border-bottom:1px solid #252b2f;display:flex;align-items:center;justify-content:space-between;gap:12px`
export const CardTitle = styled.h2`margin:0;font:600 13px Manrope,sans-serif;letter-spacing:-.15px;display:flex;align-items:center;gap:9px;svg{width:16px;height:16px;color:#abb3aa}`
export const CardBody = styled.div`padding:18px 19px`
export const Badge = styled.span<{ $tone?: 'green'|'amber'|'muted' }>`border:1px solid ${p=>p.$tone==='green'?'#405b2c':p.$tone==='amber'?'#66522e':'#363d40'};background:${p=>p.$tone==='green'?'#202a1a':p.$tone==='amber'?'#2b2419':'#202528'};color:${p=>p.$tone==='green'?'#c6f36b':p.$tone==='amber'?'#e6bd69':'#a0a9a8'};padding:4px 8px;border-radius:100px;font:10px 'DM Mono',monospace;white-space:nowrap`
export const Dropzone = styled.label`display:flex;align-items:center;gap:14px;padding:15px;border:1px dashed #3a4345;border-radius:9px;background:#101518;cursor:pointer;transition:.18s;&:hover{border-color:#c6f36b55;background:#141b18}input{display:none}`
export const UploadIcon = styled.div`width:38px;height:38px;border:1px solid #303a38;border-radius:9px;background:#1b2420;color:#c6f36b;display:grid;place-items:center;flex:none;svg{width:17px;height:17px}`
export const DropCopy = styled.div`strong{display:block;font-size:12px;font-weight:600;color:#e2e7e0}small{display:block;color:#78817f;font-size:10px;margin-top:5px}`
export const ProfileGrid = styled.div`display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:15px;@media(max-width:650px){grid-template-columns:1fr}`
export const Field = styled.label`display:grid;gap:7px;color:#858e91;font:10px 'DM Mono',monospace;letter-spacing:.35px;input,textarea{width:100%;border:1px solid #30373b;background:#0f1417;border-radius:7px;padding:10px 11px;color:#e7ebe5;font:12px 'DM Sans',sans-serif;outline:none;resize:vertical;transition:.16s;&:focus{border-color:#819b59;box-shadow:0 0 0 3px #c6f36b12}}textarea{min-height:68px;line-height:1.5}`
export const Chip = styled.span`display:inline-flex;align-items:center;border:1px solid #353d3d;border-radius:5px;background:#1a2021;padding:5px 8px;color:#bec5bc;font:10px 'DM Mono',monospace`
export const ChipRow = styled.div`display:flex;flex-wrap:wrap;gap:7px`
export const ModeCard = styled.button<{ $selected?: boolean }>`text-align:left;border:1px solid ${p=>p.$selected?'#819b59':'#30373b'};background:${p=>p.$selected?'#1b241b':'#111619'};padding:13px;border-radius:9px;color:#eff2e9;transition:.18s;&:hover{border-color:#829957}strong{display:flex;align-items:center;gap:8px;font-size:12px;font-weight:600}strong svg{width:15px;height:15px;color:${p=>p.$selected?'#c6f36b':'#929b98'}}small{display:block;color:#81898b;font-size:10px;line-height:1.55;margin-top:7px}`
export const ModeGrid = styled.div`display:grid;grid-template-columns:repeat(3,1fr);gap:9px;@media(max-width:700px){grid-template-columns:1fr}`
export const Row = styled.div`display:flex;align-items:center;justify-content:space-between;gap:12px`
export const Divider = styled.div`height:1px;background:#282f32;margin:15px 0`
export const VersionRow = styled.div`display:flex;align-items:center;gap:11px;padding:12px 0;border-bottom:1px solid #252c2f;&:last-child{border-bottom:0;padding-bottom:0}&:first-child{padding-top:0}`
export const Dot = styled.div<{ $active?: boolean }>`width:8px;height:8px;border-radius:50%;background:${p=>p.$active?'#c6f36b':'#65706f'};box-shadow:${p=>p.$active?'0 0 10px #c6f36b88':'none'};flex:none`
export const VersionInfo = styled.div`flex:1;min-width:0;strong{display:block;font-size:11px;font-weight:600}small{display:block;color:#737c7f;font:9px 'DM Mono',monospace;margin-top:4px}`
export const Preview = styled.div`position:relative;min-height:500px;background:#e8e9e4;color:#18201d;border-radius:10px;overflow:hidden;font-family:Manrope,sans-serif`
export const PreviewTop = styled.div`height:38px;background:#d9dad4;display:flex;align-items:center;padding:0 12px;gap:5px;border-bottom:1px solid #c9cbc3` 
export const BrowserDot = styled.span`width:7px;height:7px;border-radius:50%;background:#adb0a8`
export const Address = styled.div`height:21px;flex:1;margin-left:7px;background:#e9eae5;border-radius:4px;display:flex;align-items:center;padding:0 9px;color:#80867e;font:8px 'DM Mono',monospace`
export const PreviewBody = styled.div`padding:34px 23px 24px;min-height:460px;position:relative;overflow:hidden;&:after{content:'';position:absolute;width:175px;height:175px;right:-83px;top:83px;border-radius:50%;background:#c6f36b;filter:blur(60px);opacity:.42}`
export const PreviewNav = styled.div`display:flex;align-items:center;justify-content:space-between;font:700 9px Manrope,sans-serif;position:relative;z-index:1` 
export const PreviewBadge = styled.span`color:#687569;font:7px 'DM Mono',monospace;border:1px solid #b8beb1;border-radius:50px;padding:5px 7px`
export const PreviewName = styled.h3`margin:42px 0 8px;font:800 clamp(28px,3vw,41px) Manrope,sans-serif;letter-spacing:-2.2px;line-height:1.04;position:relative;z-index:1;span{color:#75834f}`
export const PreviewText = styled.p`margin:0;color:#63706b;font:10px/1.7 'DM Sans',sans-serif;max-width:250px;position:relative;z-index:1`
export const PreviewLink = styled.div`margin-top:19px;display:inline-flex;align-items:center;gap:5px;border-radius:5px;background:#19231c;color:#d5f783;padding:8px 10px;font:700 8px Manrope,sans-serif;position:relative;z-index:1`
export const PreviewSection = styled.div`position:relative;z-index:1;margin-top:36px;border-top:1px solid #c8cec2;padding-top:12px;span{font:7px 'DM Mono',monospace;color:#7e887d;text-transform:uppercase;letter-spacing:.8px}div{display:flex;gap:6px;margin-top:10px;flex-wrap:wrap}`
export const Toast = styled.div<{ $error?: boolean }>`position:fixed;right:22px;bottom:22px;z-index:5;max-width:360px;padding:12px 15px;border-radius:9px;background:${p=>p.$error?'#39211f':'#202a1b'};border:1px solid ${p=>p.$error?'#70423c':'#496031'};color:${p=>p.$error?'#f0b6aa':'#d6f19c'};font-size:12px;box-shadow:0 10px 35px #0007`
export const ModalShade = styled.div`position:fixed;inset:0;z-index:10;background:#080a0bd9;display:grid;place-items:center;padding:18px`
export const Modal = styled.div`width:min(420px,100%);border:1px solid #333c3d;background:#151a1e;border-radius:13px;padding:23px;box-shadow:0 22px 80px #0009`
export const Steps = styled.div`display:grid;grid-template-columns:repeat(4,1fr);margin:0 0 22px;border:1px solid #272e32;background:#13181c;border-radius:11px;padding:8px;@media(max-width:650px){grid-template-columns:1fr 1fr;gap:5px}`
export const StepButton = styled.button<{ $active?: boolean; $done?: boolean }>`border:0;border-radius:8px;padding:12px 10px;background:${p=>p.$active?'#202a1c':'transparent'};color:${p=>p.$active?'#e6f2d9':p.$done?'#b5c09d':'#798184'};display:flex;align-items:center;gap:10px;text-align:left;transition:.18s;&:disabled{cursor:default}.number{width:25px;height:25px;border-radius:50%;border:1px solid ${p=>p.$active||p.$done?'#829b56':'#3a4245'};color:${p=>p.$active||p.$done?'#c6f36b':'#7b8588'};display:grid;place-items:center;font:10px 'DM Mono',monospace;flex:none}strong{font-size:11px;font-weight:600}small{display:block;color:#737d80;font-size:9px;margin-top:4px}@media(max-width:650px){padding:9px 7px}`
export const StepContent = styled.div`min-height:400px`
export const SectionTitle = styled.h2`font:600 18px Manrope,sans-serif;letter-spacing:-.4px;margin:0;color:#eff2e9`
export const SectionNote = styled.p`color:#8a9395;font-size:12px;line-height:1.65;margin:7px 0 19px;max-width:620px`
export const DefinitionRow = styled.div`display:grid;grid-template-columns:minmax(125px,.85fr) minmax(180px,1.2fr) minmax(150px,1fr) 34px;gap:9px;align-items:start;padding:13px 0;border-bottom:1px solid #262d30;&:last-child{border-bottom:0}@media(max-width:750px){grid-template-columns:1fr 1fr 34px;& > :nth-child(2){grid-column:1/3;grid-row:2}& > :nth-child(3){grid-column:1/3;grid-row:3}}`
export const DefinitionInput = styled.input`width:100%;border:1px solid #30373b;background:#0f1417;border-radius:7px;padding:10px;color:#e7ebe5;font:12px 'DM Sans',sans-serif;outline:none;&:focus{border-color:#819b59;box-shadow:0 0 0 3px #c6f36b12}`
export const DefinitionArea = styled.textarea`width:100%;min-height:65px;border:1px solid #30373b;background:#0f1417;border-radius:7px;padding:10px;color:#e7ebe5;font:11px/1.5 'DM Mono',monospace;outline:none;resize:vertical;&:focus{border-color:#819b59;box-shadow:0 0 0 3px #c6f36b12}`
export const RowCaption = styled.div`color:#818a8c;font:9px 'DM Mono',monospace;text-transform:uppercase;letter-spacing:.5px;margin:0 0 6px`
export const JsonValue = styled.textarea`width:100%;min-height:94px;border:1px solid #30373b;background:#0f1417;border-radius:7px;padding:11px;color:#d7e2d0;font:11px/1.55 'DM Mono',monospace;outline:none;resize:vertical;&:focus{border-color:#819b59;box-shadow:0 0 0 3px #c6f36b12}`
export const DataHeader = styled.div`display:grid;grid-template-columns:minmax(110px,.7fr) minmax(150px,1fr) 74px minmax(220px,1.5fr) 34px;gap:11px;padding:0 10px 9px;color:#788284;font:9px 'DM Mono',monospace;text-transform:uppercase;letter-spacing:.55px;@media(max-width:800px){display:none}`
export const DataRow = styled.div`display:grid;grid-template-columns:minmax(110px,.7fr) minmax(150px,1fr) 74px minmax(220px,1.5fr) 34px;gap:11px;align-items:start;padding:12px 10px;border-top:1px solid #252c30;&:first-of-type{border-top:0}@media(max-width:800px){grid-template-columns:1fr 34px;& > :nth-child(2){grid-column:1/3;grid-row:2}& > :nth-child(3){grid-column:1;grid-row:3}& > :nth-child(4){grid-column:1/3;grid-row:4}}`
export const StepFooter = styled.div`display:flex;justify-content:space-between;align-items:center;gap:12px;margin-top:21px;padding-top:16px;border-top:1px solid #282f32;@media(max-width:500px){align-items:stretch;flex-direction:column-reverse}`
export const AsideBlock = styled.div`display:grid;gap:10px`
export const JsonPreview = styled.pre`margin:0;max-height:320px;overflow:auto;background:#0d1214;border:1px solid #272f32;border-radius:8px;padding:13px;color:#b9d59c;font:10px/1.65 'DM Mono',monospace;white-space:pre-wrap;word-break:break-word`
